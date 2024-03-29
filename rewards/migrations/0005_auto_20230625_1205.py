# Generated by Django 3.2.18 on 2023-06-25 07:05

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0004_auto_20230619_0211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='monsterhunter',
            name='turn_available',
            field=models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AlterField(
            model_name='spinwheel',
            name='spin_available',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='ticktactoe',
            name='turn_available',
            field=models.PositiveIntegerField(default=10, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(20)]),
        ),
    ]
