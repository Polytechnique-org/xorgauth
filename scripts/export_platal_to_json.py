#!/usr/bin/env python3
"""Export the data needed for auth in JSON format, from Plat/al database

Requires:
    pip install PyMySQL
    platal.conf file
"""
from collections import OrderedDict
import configparser
import pymysql
import json
import sys


# Load platal.conf and connect
conf = configparser.SafeConfigParser()
conf.read('platal.conf')
db = pymysql.connect(
    host=conf['Core']['dbhost'].strip('"'),
    user=conf['Core']['dbuser'].strip('"'),
    password=conf['Core']['dbpwd'].strip('"'),
    db=conf['Core']['dbdb'].strip('"'),
    charset='utf8mb4',
)

result = {
    'authgroupex': [],
    'accounts': [],
}


def get_cols_from_query(query):
    select_part = query.split(' FROM', 1)[0].split('SELECT', 1)[1]
    return [p.split()[-1].split('.')[-1] for p in select_part.split(',')]


# Export authgroupex info
with db.cursor() as cursor:
    print("Exporting group_auth table")
    sql = """
        SELECT  ga.privkey, ga.name, ga.datafields, ga.returnurls, ga.flags,
                g.diminutif AS groupid, g.nom AS groupname
          FROM  group_auth AS ga
     LEFT JOIN  groups AS g ON (g.id = ga.group_id)
    """
    cols = get_cols_from_query(sql)
    cursor.execute(sql)
    for row in cursor:
        entry = OrderedDict(zip(cols, row))
        result['authgroupex'].append(entry)

# Export accounts info
accounts = OrderedDict()
with db.cursor() as cursor:
    print("Exporting accounts table")
    sql = """
        SELECT  a.uid, a.hruid, a.password, a.type, a.is_admin,
                a.firstname, a.lastname, a.full_name, a.directory_name, a.display_name,
                a.sex, a.email, a.state,
                p.ax_id, p.xorg_id, pd.promo, pe.grad_year
          FROM  accounts AS a
     LEFT JOIN  account_profiles AS ap ON (ap.uid = a.uid AND FIND_IN_SET('owner', ap.perms))
     LEFT JOIN  profiles AS p ON (p.pid = ap.pid)
     LEFT JOIN  profile_display AS pd ON (pd.pid = p.pid)
     LEFT JOIN  profile_education AS pe ON (pe.pid = p.pid AND FIND_IN_SET(\'primary\', pe.flags))
         WHERE  a.state IN ('active', 'pending') AND p.deathdate IS NULL
      GROUP BY  a.uid
     """
    cols = get_cols_from_query(sql)
    cursor.execute(sql)
    for row in cursor:
        entry = OrderedDict(zip(cols, row))
        uid = int(entry['uid'])
        if entry['xorg_id'] == 0:
            entry['xorg_id'] = None
        if entry['ax_id'] == '':
            entry['ax_id'] = None
        entry['email_source'] = OrderedDict()
        entry['email_redirect'] = OrderedDict()
        entry['groups'] = OrderedDict()
        accounts[uid] = entry

with db.cursor() as cursor:
    print("Exporting email_source_account table")
    sql = """
        SELECT  s.uid, s.type, CONCAT(s.email, '@', d.name) AS email, s.flags
          FROM  email_source_account  AS s
    INNER JOIN  email_virtual_domains AS m ON (s.domain = m.id)
    INNER JOIN  email_virtual_domains AS d ON (d.aliasing = m.id)
      ORDER BY  s.uid, d.id
    """
    cursor.execute(sql)
    for uid, stype, email, flags in cursor:
        uid = int(uid)
        if uid not in accounts:
            # Skip disabled accounts
            continue
        assert email not in accounts[uid]['email_source']
        accounts[uid]['email_source'][email] = stype
        if 'bestalias' in flags and accounts[uid]['email'] is None:
            accounts[uid]['email'] = email

with db.cursor() as cursor:
    print("Exporting email_redirect_account table")
    sql = """
        SELECT  r.uid, r.type, r.redirect
          FROM  email_redirect_account AS r
         WHERE  r.type != 'homonym'
    """
    cursor.execute(sql)
    for uid, rtype, email in cursor:
        uid = int(uid)
        if uid not in accounts:
            continue
        assert email not in accounts[uid]['email_redirect']
        accounts[uid]['email_redirect'][email] = rtype

with db.cursor() as cursor:
    print("Exporting group_members table")
    sql = """
        SELECT  gm.uid, g.diminutif AS groupid, gm.perms
          FROM  group_members AS gm
    INNER JOIN  groups AS g ON (g.id = gm.asso_id)
    """
    cursor.execute(sql)
    for uid, groupid, perms in cursor:
        uid = int(uid)
        if uid not in accounts:
            continue
        # Use English
        if perms == 'membre':
            perms = 'member'
        assert groupid not in accounts[uid]['groups']
        accounts[uid]['groups'][groupid] = perms

print("Removing pending accounts without email addresses")
is_data_valid = True
user_for_email = {}  # ensure that "email" field is unique
for uid in list(accounts.keys()):
    user = accounts[uid]
    if not user['email']:
        if user['state'] != 'pending':
            print("Warning: account %r does not have an email address" % user['hruid'])
        del accounts[uid]
        continue

    other_user = user_for_email.get(user['email'])
    if other_user is None:
        # Easy case: the email has not been already seen
        user_for_email[user['email']] = user
        continue

    other_uid = other_user['uid']
    # Two users share the same email address
    # This can occur if one of them is pending
    best_uid = None
    if user['state'] == 'pending':
        best_uid = other_uid
    elif other_user['state'] == 'pending':
        best_uid = uid
    else:
        # Some users have two accounts, like:
        # - a FX member who also has an external account
        # - some external accounts who changed their email
        # Find the best matching account for them
        if user['type'] == 'xnet' and other_user['type'] != 'xnet':
            best_uid = other_uid
        elif user['type'] != 'xnet' and other_user['type'] == 'xnet':
            best_uid = uid
        elif user['type'] == 'xnet' and other_user['type'] == 'xnet':
            # Make the hruid from the email address and compare
            # NB: at the time of writing this, there were only 2 accounts in
            # such a situation
            assert user['hruid'] != other_user['hruid'], "hruid is not unique in the database!"
            hruid_from_email = user['email'].lower().replace('@', '.') + '.ext'
            if hruid_from_email == user['hruid']:
                best_uid = uid
            elif hruid_from_email == other_user['hruid']:
                best_uid = uid

    if best_uid is None:
        print("Error: accounts %r and %r share the same email address %r!" % (
            user['hruid'], other_user['hruid'], user['email']))
        is_data_valid = False
        continue

    # Merge the groups
    if best_uid == uid:
        user['groups'].update(other_user['groups'])
        del accounts[other_uid]
        user_for_email[user['email']] = user
    else:
        other_user['groups'].update(user['groups'])
        del accounts[uid]

if not is_data_valid:
    sys.exit(1)

result['accounts'] = list(accounts.values())

# Output JSON
print("Writing JSON file")
with open('exported_for_auth.json', 'w') as f:
    json.dump(result, f, indent=2)
