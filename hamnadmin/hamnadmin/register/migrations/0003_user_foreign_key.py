# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('register', '0002_cleanup_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.RunSQL("UPDATE feeds SET user_id=(SELECT id FROM auth_user WHERE auth_user.username=userid)"),
        migrations.AlterField(
            model_name='blog',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.RemoveField(
            model_name='blog',
            name='userid',
        ),
    ]
