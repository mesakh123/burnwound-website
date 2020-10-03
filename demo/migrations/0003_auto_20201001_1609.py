# Generated by Django 2.2.10 on 2020-10-01 08:09

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0002_auto_20201001_1531'),
    ]

    operations = [
        migrations.AddField(
            model_name='burndocument',
            name='file_location',
            field=models.CharField(default='', max_length=2048),
        ),
        migrations.AddField(
            model_name='handdocument',
            name='file_location',
            field=models.CharField(default='', max_length=2048),
        ),
        migrations.AlterField(
            model_name='patientdata',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2020, 10, 1, 16, 9, 55, 858152), verbose_name='Created Date'),
        ),
    ]
