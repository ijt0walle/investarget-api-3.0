# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-08-02 10:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sourcetype', '0021_auto_20170802_1043'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ProjService',
            new_name='Service',
        ),
    ]