# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-06-21 13:53
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.deletion
import utils.customClass


class Migration(migrations.Migration):

    dependencies = [
        ('proj', '0025_auto_20170621_1346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='proj',
            field=utils.customClass.MyForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proj_attachment', to='proj.project'),
        ),
    ]
