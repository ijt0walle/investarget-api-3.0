# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-05-05 16:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usersys', '0019_userfriendship_accepttime'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userfriendship',
            options={'permissions': ()},
        ),
        migrations.AlterModelTable(
            name='userfriendship',
            table='user_friendship',
        ),
    ]