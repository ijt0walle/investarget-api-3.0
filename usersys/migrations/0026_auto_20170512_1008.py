# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-05-12 10:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usersys', '0025_auto_20170512_0955'),
    ]

    operations = [
        migrations.RenameField(
            model_name='myuser',
            old_name='userstatu',
            new_name='userstatus',
        ),
    ]
