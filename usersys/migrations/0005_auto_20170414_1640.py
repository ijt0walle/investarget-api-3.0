# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-04-14 16:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usersys', '0004_auto_20170414_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='mobileAreaCode',
            field=models.CharField(blank=True, default='86', max_length=10, null=True),
        ),
    ]