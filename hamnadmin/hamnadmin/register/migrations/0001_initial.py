# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AggregatorLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ts', models.DateTimeField(auto_now=True)),
                ('success', models.BooleanField()),
                ('info', models.TextField()),
            ],
            options={
                'ordering': ['-ts'],
                'db_table': 'aggregatorlog',
            },
        ),
        migrations.CreateModel(
            name='AuditEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('logtime', models.DateTimeField(default=datetime.datetime.now)),
                ('user', models.CharField(max_length=32)),
                ('logtxt', models.CharField(max_length=1024)),
            ],
            options={
                'ordering': ['logtime'],
                'db_table': 'auditlog',
            },
        ),
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('feedurl', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('blogurl', models.CharField(max_length=255)),
                ('lastget', models.DateTimeField(default=datetime.datetime(2000, 1, 1, 0, 0))),
                ('userid', models.CharField(max_length=255)),
                ('approved', models.BooleanField()),
                ('authorfilter', models.CharField(default=b'', max_length=255, blank=True)),
                ('twitteruser', models.CharField(default=b'', max_length=255, blank=True)),
                ('excludestats', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['approved', 'name'],
                'db_table': 'feeds',
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('guid', models.CharField(max_length=255)),
                ('link', models.CharField(max_length=255)),
                ('txt', models.TextField()),
                ('dat', models.DateTimeField()),
                ('title', models.CharField(max_length=255)),
                ('guidisperma', models.BooleanField()),
                ('hidden', models.BooleanField()),
                ('twittered', models.BooleanField()),
                ('shortlink', models.CharField(max_length=255)),
                ('feed', models.ForeignKey(related_name='posts', db_column=b'feed', to='register.Blog')),
            ],
            options={
                'ordering': ['-dat'],
                'db_table': 'posts',
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('teamurl', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'teams',
            },
        ),
        migrations.AddField(
            model_name='blog',
            name='team',
            field=models.ForeignKey(db_column=b'team', blank=True, to='register.Team', null=True),
        ),
        migrations.AddField(
            model_name='aggregatorlog',
            name='feed',
            field=models.ForeignKey(to='register.Blog', db_column=b'feed'),
        ),
    ]
