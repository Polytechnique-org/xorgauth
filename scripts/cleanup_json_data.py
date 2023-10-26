#!/usr/bin/env python
import collections
import json

with open('exported_for_auth.json', 'r') as f:
    data = json.load(f, object_pairs_hook=collections.OrderedDict)

# Astrid Lange has two accounts with the same email address
astrid_lange = [d for d in data['accounts'] if d['email'] == 'astrid.lange@polytechnique.edu']
if len(astrid_lange) != 1:
        assert len(astrid_lange) == 2
        assert astrid_lange[0]['type'] == 'xnet'
        assert astrid_lange[1]['type'] == 'fx'
        # Remove the xnet account
        astrid_lange[1]['groups'].update(astrid_lange[0]['groups'])
        data['accounts'].remove(astrid_lange[0])

# Jean Boisson
jb = [d for d in data['accounts'] if d['email'] == 'jeanboisson@yahoo.fr']
if len(jb) != 1:
        assert len(jb) == 2
        assert all(d['type'] == 'xnet' for d in jb)
        assert jb[0]['hruid'] == 'boisson.ens.fr.ext'
        assert jb[1]['hruid'] == 'jeanboisson.yahoo.fr.ext'
        jb[1]['groups'].update(jb[0]['groups'])
        data['accounts'].remove(jb[0])

# veronique.mary-lavergne@ax.polytechnique.org
vml = [d for d in data['accounts'] if d['email'] == 'veronique.mary-lavergne@ax.polytechnique.org']
if len(vml) != 1:
        assert len(vml) == 2
        assert vml[0]['hruid'] == 'veroniquemarylavergne.amicale.polytechnique.org.ext'
        assert vml[1]['hruid'] == 'veronique.mary-lavergne.ax.polytechnique.org.ext'
        # copy names
        for k, v in vml[0].items():
            if 'name' in k:
                assert isinstance(v, unicode)
                vml[1][k] = v
        vml[1]['groups'].update(vml[0]['groups'])
        data['accounts'].remove(vml[0])

# raphael.guimares-feijo.2016 has invalid email
#rgf = [d for d in data['accounts'] if d['email'] == 'raphael.@polytechnique.org']
#assert len(rgf) == 1
#rgf[0]['email'] = 'raphael.guimares-feijo.2016@polytechnique.org'
#rgf[0]['email_source'] = collections.OrderedDict((k, v) for (k, v) in rgf[0]['email_source'].items() if '.@' not in k and '..' not in k)

# replace 0 with null in xorg_id
#for d in data['accounts']:
#    if d['xorg_id'] == 0:
#        d['xorg_id'] = None  # TODO: check in django

# check email unicity
found_emails = dict((d['email'], d) for d in data['accounts'])
for d in data['accounts']:
    d2 = found_emails[d['email']]
    if d != d2:
        print("Found error for %s:" % d['email'])
        print(repr(d))
        print(repr(d2))

# raphael.guimaraes-feijao.2016 is a duplicate with raphael.guimares-feijo.2016
# TODO: contact him and see what's wrong (-- IooNag 2018-04-07)
rgf = [d for d in data['accounts'] if d['hruid'] == 'raphael.guimaraes-feijao.2016']
if len(rgf):
    data['accounts'].remove(rgf[0])

# 2021-02-04 remove false duplicate due to dead people
# 2021-04-21 remove olivier.certner@polytechnique.orgJ and benigne.gmail.com accounts
to_remove = [d for d in data['accounts'] \
	if (d['hruid'] == 'pratmarca.orange.fr.ext' and d['email'] == 'pratmarca@orange.fr') or \
           (d['hruid'] == 'map2k.free.fr.ext' and d['email'] == 'map2k@free.fr') or \
           (d['hruid'] == 's.rizk.ga-sa.fr.ext' and d['email'] == 's.rizk@ga-sa.fr') or \
           (d['hruid'] == 'olivier.certner.polytechnique.orgj.ext' and d['email'] == 'olivier.certner@polytechnique.orgJ') or \
           (d['hruid'] == 'benigne.deprey.mines-paris.org.ext' and d['email'] == 'benigne.gmail.com')]
for d in to_remove:
    #print("Removing dead people: %r" % to_remove)
    data['accounts'].remove(d)
del to_remove


# save
with open('exported_for_auth.clean.json', 'w') as f:
    json.dump(data, f, indent=2)
print("Cleaned data saved into exported_for_auth.clean.json (%d accounts, %d authgroupex)" % (len(data['accounts']), len(data['authgroupex'])))
