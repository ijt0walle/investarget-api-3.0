# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-05-12 09:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('org', '0013_auto_20170512_0939'),
    ]

    operations = [
        migrations.RenameField(
            model_name='organization',
            old_name='orgStatus',
            new_name='orgstatus',
        ),
    ]
