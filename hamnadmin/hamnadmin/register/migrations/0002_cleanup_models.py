# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='approved',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='post',
            name='guidisperma',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='post',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='post',
            name='twittered',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name='post',
            unique_together=set([('id', 'guid')]),
        ),
    ]
