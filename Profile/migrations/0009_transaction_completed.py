# Generated by Django 3.2.18 on 2023-05-19 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Profile', '0008_alter_profile_dob'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='completed',
            field=models.BooleanField(default=False),
        ),
    ]
