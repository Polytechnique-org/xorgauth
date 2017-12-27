import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from xorgauth.authgroupex.models import AuthGroupeXClient


class Command(BaseCommand):
    help = "Import a JSON file with authgroupex client data into the database"

    def add_arguments(self, parser):
        parser.add_argument('jsonfile', nargs=1, type=str,
                            help="path to JSON file to load")

    def handle(self, *args, **options):
        with open(options['jsonfile'][0], 'r') as jsonfd:
            jsondata = json.load(jsonfd)
        if 'authgroupex' not in jsondata:
            raise CommandError("Unable to find account entries")
        for client_data in jsondata['authgroupex']:
            name = client_data['name']
            try:
                client = AuthGroupeXClient.objects.get(name=name)
            except ObjectDoesNotExist:
                client = AuthGroupeXClient(name=name)

            client.privkey = client_data['privkey']
            client.datafields = client_data['datafields']
            client.returnurls = client_data['returnurls']
            client.allow_xnet = (client_data['flags'] == 'allow_xnet')
            client.save()
