# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-06-06 19:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('APIlog', '0005_auto_20170606_1902'),
    ]

    operations = [
        migrations.RenameField(
            model_name='apilog',
            old_name='modelID',
            new_name='model_id',
        ),
        migrations.RenameField(
            model_name='apilog',
            old_name='modelName',
            new_name='model_name',
        ),
        migrations.RenameField(
            model_name='apilog',
            old_name='requestuserid',
            new_name='requestuser_id',
        ),
        migrations.RenameField(
            model_name='apilog',
            old_name='requestusername',
            new_name='requestuser_name',
        ),
    ]