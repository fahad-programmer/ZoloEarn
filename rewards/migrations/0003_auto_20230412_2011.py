# Generated by Django 3.2.18 on 2023-04-12 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0002_monsterhunter_ticktactoe'),
    ]

    operations = [
        migrations.AddField(
            model_name='monsterhunter',
            name='last_played_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='spinwheel',
            name='last_played_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticktactoe',
            name='last_played_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]