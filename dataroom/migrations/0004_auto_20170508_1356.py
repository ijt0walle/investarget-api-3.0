# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-05-08 13:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataroom', '0003_auto_20170505_1641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataroomdirectoryorfile',
            name='parent',
            field=models.ForeignKey(blank=True, help_text='\u76ee\u5f55\u6216\u6587\u4ef6\u6240\u5c5e\u76ee\u5f55id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='asparent_directories', to='dataroom.dataroomdirectoryorfile'),
        ),
    ]