# Generated by Django 2.2.10 on 2020-10-01 08:18

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0005_auto_20201001_1618'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientdata',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2020, 10, 1, 16, 18, 56, 513628), verbose_name='Created Date'),
        ),
    ]
