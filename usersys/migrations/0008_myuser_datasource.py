# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-04-19 16:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sourcetype', '0002_auto_20170419_1605'),
        ('usersys', '0007_auto_20170418_0931'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='datasource',
            field=models.ForeignKey(default=1, help_text='\u6570\u636e\u6e90', on_delete=django.db.models.deletion.CASCADE, to='sourcetype.DataSource'),
            preserve_default=False,
        ),
    ]