# Generated by Django 3.2.17 on 2023-02-23 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Profile', '0013_alter_recentearnings_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='recentearnings',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]