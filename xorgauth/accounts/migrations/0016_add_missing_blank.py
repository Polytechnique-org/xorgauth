# Generated by Django 2.0.3 on 2018-03-11 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_add_gapps_password'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='xorgdb_uid',
            field=models.IntegerField(blank=True, help_text='User ID in Polytechnique.org database',
                                      null=True, unique=True, verbose_name='Polytechnique.org database user ID'),
        ),
    ]
