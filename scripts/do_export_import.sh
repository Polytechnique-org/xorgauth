#!/bin/sh
set -x -e
./export_platal_to_json.py
./cleanup_json_data.py
python ../manage.py importaccounts exported_for_auth.clean.json
rm exported_for_auth.json
rm exported_for_auth.clean.json
echo "DONE"
