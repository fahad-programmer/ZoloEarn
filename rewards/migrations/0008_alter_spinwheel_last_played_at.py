# Generated by Django 3.2.18 on 2023-04-12 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0007_alter_spinwheel_last_played_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spinwheel',
            name='last_played_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]