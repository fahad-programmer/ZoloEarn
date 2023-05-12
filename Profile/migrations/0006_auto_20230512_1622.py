# Generated by Django 3.2.18 on 2023-05-12 11:22

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Profile', '0005_auto_20230510_2156'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='country',
            field=models.CharField(blank=True, default='China', max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='profile_pic_path',
            field=models.CharField(blank=True, default=1, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='referral',
            name='signed_up_at',
            field=models.DateField(default=datetime.date(2023, 5, 12)),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='created_at',
            field=models.DateField(default=datetime.date(2023, 5, 12)),
        ),
    ]
