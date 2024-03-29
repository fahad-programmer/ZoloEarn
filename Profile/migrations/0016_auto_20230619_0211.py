# Generated by Django 3.2.18 on 2023-06-18 21:11

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Profile', '0015_auto_20230612_2113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recentearnings',
            name='created_at',
            field=models.DateField(default=datetime.date(2023, 6, 18)),
        ),
        migrations.AlterField(
            model_name='referral',
            name='signed_up_at',
            field=models.DateField(default=datetime.date(2023, 6, 18)),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='created_at',
            field=models.DateField(default=datetime.date(2023, 6, 18)),
        ),
    ]
