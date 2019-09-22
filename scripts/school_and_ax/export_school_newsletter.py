#!/usr/bin/env python3
"""Export the data needed for the school to send its newsletter to the subscribers

Requires:
    pip install PyMySQL
    platal.conf file in the parent folder (shared with ../export_platal_to_json.py)
"""
import configparser
import csv
import datetime
import os.path
import re

import pymysql


# Load platal.conf and connect
conf = configparser.SafeConfigParser()
conf.read(os.path.join(os.path.dirname(__file__), '..', 'platal.conf'))
db = pymysql.connect(
    host=conf['Core']['dbhost'].strip('"'),
    user=conf['Core']['dbuser'].strip('"'),
    password=conf['Core']['dbpwd'].strip('"'),
    db=conf['Core']['dbdb'].strip('"'),
    charset='utf8mb4',
)


# Check that the school newsletter has the expected ID
SCHOOL_NL_ID = 2
with db.cursor() as cursor:
    sql = """
        SELECT  n.name, g.diminutif
          FROM  newsletters AS n
    INNER JOIN  groups AS g ON (g.id = n.group_id)
         WHERE  n.id = %s
    """
    cursor.execute(sql, SCHOOL_NL_ID)
    rows = cursor.fetchall()
    if rows != (("Lettre de l'École polytechnique", "Ecole"), ):
        raise RuntimeError("The school newsletter does not have ID {}: {}".format(SCHOOL_NL_ID, rows))


# Create a CSV file
csv_name = datetime.datetime.now().strftime('%Y-%m-%d_export_dixit.csv')
with open(csv_name, 'w', newline='', encoding='utf-8') as fout:
    csv_stream = csv.writer(fout, delimiter=';', quotechar='"', escapechar='\\', quoting=csv.QUOTE_MINIMAL)
    csv_stream.writerow(("Prénom", "Nom", "Promotion", "Adresse"))

    # Export subscribers
    with db.cursor() as cursor:
        sql = """
           SELECT  a.firstname, a.lastname, pd.promo, CONCAT(s.email, '_ecole@', d.name) AS email
             FROM  newsletter_ins AS ni
        LEFT JOIN  accounts AS a ON (a.uid = ni.uid)
        LEFT JOIN  account_profiles AS ap ON (ap.uid = a.uid AND FIND_IN_SET('owner', ap.perms))
        LEFT JOIN  profiles AS p ON (p.pid = ap.pid)
        LEFT JOIN  profile_display AS pd ON (pd.pid = p.pid)
        LEFT JOIN  email_source_account AS s ON (s.uid = a.uid AND s.type = 'forlife')
        LEFT JOIN  email_virtual_domains AS m ON (s.domain = m.id)
        LEFT JOIN  email_virtual_domains AS d ON (d.aliasing = m.id)
            WHERE  ni.nlid = %s
                   AND p.deathdate IS NULL
                   AND pd.promo IS NOT NULL
                   AND d.name = "alumni.polytechnique.org"
        """
        cursor.execute(sql, SCHOOL_NL_ID)
        for row in cursor:
            # Sanity checks before adding a row, in order to make sure we do not transmit invalid data to the school
            firstname, lastname, promo, email = row

            name_charset = r"[^'.a-zA-ZÁÇÉÖàáâãäåçèéêëíîïñóôöúüÿ -]"
            invalid_characters = set(re.findall(name_charset, firstname))
            if invalid_characters:
                print("Warning: invalid characters in firstname %r: %r" % (firstname, invalid_characters))

            invalid_characters = set(re.findall(name_charset, lastname))
            if invalid_characters:
                print("Warning: invalid characters in lastname %r: %r" % (lastname, invalid_characters))

            invalid_characters = set(re.findall(r'[^0-9BDEGMX ]', promo.replace('D (en cours)', '')))
            if invalid_characters:
                print("Warning: invalid characters in promo %r: %r" % (promo, invalid_characters))

            if not email.endswith('_ecole@alumni.polytechnique.org'):
                print("Warning: invalid email suffix: %r" % email)
            else:
                invalid_characters = set(re.findall(r'[^0-9a-z.-]', email[:-len('_ecole@alumni.polytechnique.org')]))
                if invalid_characters:
                    print("Warning: invalid characters in email %r: %r" % (email, invalid_characters))
                else:
                    if not re.match(r'^([a-z-]+\.){2,3}[a-z0-9]+_ecole@alumni\.polytechnique\.org$', email):
                        print("Warning: unexpect format of email address %r" % email)

            csv_stream.writerow(row)

print("Exported data in {}".format(csv_name))
