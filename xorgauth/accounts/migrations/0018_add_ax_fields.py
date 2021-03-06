# Generated by Django 2.2 on 2019-05-05 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_add_user_profile_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='ax_contributor',
            field=models.NullBooleanField(help_text='Paid a contribution to AX', verbose_name='AX contributor'),
        ),
        migrations.AddField(
            model_name='user',
            name='ax_last_synced',
            field=models.DateField(blank=True, null=True, verbose_name='last sync with AX'),
        ),
        migrations.AddField(
            model_name='user',
            name='axjr_subscriber',
            field=models.NullBooleanField(help_text='Subscribed to La Jaune et la Rouge',
                                          verbose_name='J&R subscriber'),
        ),
    ]
