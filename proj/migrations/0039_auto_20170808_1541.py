# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-08-08 15:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proj', '0038_auto_20170808_1121'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectindustries',
            name='bucket',
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='projectindustries',
            name='key',
            field=models.TextField(blank=True, null=True),
        ),
    ]