# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-05-05 16:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataroom', '0002_auto_20170502_1859'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dataroom',
            options={'permissions': (('admin_getdataroom', '\u7ba1\u7406\u5458\u67e5\u770bdataroom'), ('admin_changedataroom', '\u7ba1\u7406\u5458\u4fee\u6539dataroom\u91cc\u7684\u6587\u4ef6'), ('admin_deletedataroom', '\u7ba1\u7406\u5458\u5220\u9664dataroom'), ('admin_adddataroom', '\u7ba1\u7406\u5458\u6dfb\u52a0dataroom'), ('admin_closedataroom', '\u7ba1\u7406\u5458\u5173\u95eddataroom'), ('user_closedataroom', '\u7528\u6237\u5173\u95eddataroom(obj\u7ea7\u522b)'), ('user_getdataroom', '\u7528\u6237\u67e5\u770bdataroom\u5185\u7684\u6587\u4ef6\u5185\u5bb9(obj\u7ea7\u522b)'), ('user_changedataroom', '\u7528\u6237\u4fee\u6539dataroom\u5185\u7684\u6587\u4ef6\u5185\u5bb9(obj\u7ea7\u522b)'), ('user_adddataroom', '\u7528\u6237\u6dfb\u52a0dataroom(obj/class\u7ea7\u522b)'), ('user_deletedataroom', '\u7528\u6237\u5220\u9664dataroom\u5185\u7684\u6587\u4ef6\u5185\u5bb9(obj/class\u7ea7\u522b)'))},
        ),
        migrations.AlterModelOptions(
            name='dataroomdirectoryorfile',
            options={},
        ),
        migrations.AlterField(
            model_name='dataroomdirectoryorfile',
            name='parent',
            field=models.ForeignKey(blank=True, help_text='\u76ee\u5f55\u6216\u6587\u4ef6\u6240\u5c5e\u76ee\u5f55id', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='directory_directories', to='dataroom.dataroomdirectoryorfile'),
        ),
    ]