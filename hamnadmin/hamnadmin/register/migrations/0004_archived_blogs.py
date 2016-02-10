# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0003_user_foreign_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
