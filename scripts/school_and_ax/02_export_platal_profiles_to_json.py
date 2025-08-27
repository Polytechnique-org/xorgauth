#!/usr/bin/env python
"""Export the data needed for AX database in JSON format, from Plat/al database

Requires:
    pip install PyMySQL
    platal.conf file in the parent folder (shared with ../export_platal_to_json.py)
"""
from collections import OrderedDict
import configparser
import pymysql
import json
import os.path


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

result = {
    'profiles': [],
}


def get_cols_from_query(query):
    select_part = query.split(' FROM', 1)[0].split('SELECT', 1)[1]
    return [p.split()[-1].split('.')[-1] for p in select_part.split(',')]


# Export profiles information
with db.cursor() as cursor:
    print("Exporting profiles table")
    sql = """
        SELECT  p.ax_id, p.hrpid, p.xorg_id, p.sex,
                pn.lastname_main, pn.firstname_main,
                pd.public_name, pd.promo, pede.degree,
                a.state
          FROM  profiles AS p
     LEFT JOIN  profile_public_names AS pn ON pn.pid=p.pid
     LEFT JOIN  profile_display AS pd ON pd.pid=p.pid
     LEFT JOIN  profile_education AS pe ON (pe.pid = p.pid AND FIND_IN_SET(\'primary\', pe.flags))
     LEFT JOIN  profile_education_enum AS pee ON (pee.id = pe.eduid AND pee.abbreviation = 'X')
     LEFT JOIN  profile_education_degree_enum AS pede ON (pede.id = pe.degreeid AND pee.abbreviation = 'X')
     LEFT JOIN  accounts AS a ON (a.hruid = p.hrpid)
      ORDER BY  p.pid
    """
    cols = get_cols_from_query(sql)
    cursor.execute(sql)
    for row in cursor:
        entry = OrderedDict(zip(cols, row))
        result['profiles'].append(entry)

# Output JSON
print("Writing JSON file")
with open('exported_for_ax.json', 'w') as f:
    json.dump(result, f, indent=2)
