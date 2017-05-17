# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-05-16 11:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='loginlog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.PositiveIntegerField(blank=True, null=True)),
                ('loginaccount', models.CharField(blank=True, max_length=40, null=True)),
                ('logintime', models.DateTimeField(auto_now_add=True, null=True)),
                ('loginsource', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'LOG_login',
            },
        ),
        migrations.CreateModel(
            name='viewprojlog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.PositiveIntegerField(blank=True, null=True)),
                ('proj', models.PositiveIntegerField(blank=True, null=True)),
                ('viewtime', models.DateTimeField(auto_now_add=True, null=True)),
                ('source', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'LOG_userviewproject',
            },
        ),
    ]