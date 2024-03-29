# Generated by Django 3.2.18 on 2023-06-12 16:13

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Profile', '0014_alter_profile_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recentearnings',
            name='created_at',
            field=models.DateField(default=datetime.date(2023, 6, 12)),
        ),
        migrations.AlterField(
            model_name='referral',
            name='signed_up_at',
            field=models.DateField(default=datetime.date(2023, 6, 12)),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='created_at',
            field=models.DateField(default=datetime.date(2023, 6, 12)),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='points',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='HelpCenter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=1000)),
                ('message', models.CharField(max_length=10000)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
