# Generated by Django 3.2.18 on 2023-07-27 11:19

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Profile', '0024_auto_20230727_0022'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recentearnings',
            name='created_at',
            field=models.DateField(default=datetime.date(2023, 7, 27)),
        ),
        migrations.AlterField(
            model_name='referral',
            name='signed_up_at',
            field=models.DateField(default=datetime.date(2023, 7, 27)),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='created_at',
            field=models.DateField(default=datetime.date(2023, 7, 27)),
        ),
    ]