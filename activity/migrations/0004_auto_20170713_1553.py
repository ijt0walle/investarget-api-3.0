# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-07-13 15:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0003_auto_20170605_1700'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='createdtime',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]