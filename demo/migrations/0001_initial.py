# Generated by Django 2.2.10 on 2020-10-01 07:21

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PatientData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('patient_id', models.CharField(max_length=200)),
                ('age', models.IntegerField(default=0)),
                ('sex', models.CharField(choices=[('f', 'Female'), ('m', 'Male'), ('u', 'Unsure')], max_length=1)),
                ('height', models.FloatField()),
                ('weight', models.FloatField()),
                ('burn_type', models.CharField(choices=[('s', 'Scald'), ('g', 'Grease'), ('n', 'Contact'), ('f', 'Flame'), ('c', 'Chemical'), ('e', 'Electric'), ('o', 'Other')], max_length=1)),
                ('comments', models.TextField()),
                ('created', models.DateTimeField(default=datetime.datetime(2020, 10, 1, 15, 21, 35, 323666), verbose_name='Created Date')),
            ],
            options={
                'verbose_name_plural': 'PatientData',
            },
        ),
        migrations.CreateModel(
            name='PredictResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('predicted_time', models.DateTimeField(blank=True, default=datetime.datetime.now)),
            ],
        ),
        migrations.CreateModel(
            name='HandDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hand_docfile', models.ImageField(blank=True, upload_to='documents/hand/%Y/%m/%d')),
                ('hand_predict_docfile', models.ImageField(blank=True, upload_to='documents/predict/hand/%Y/%m/%d')),
                ('predicted', models.BooleanField(default=False)),
                ('hand_result', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='demo.PredictResult')),
            ],
        ),
        migrations.CreateModel(
            name='BurnDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('burn_docfile', models.ImageField(blank=True, upload_to='documents/burn/%Y/%m/%d')),
                ('burn_predict_docfile', models.ImageField(blank=True, upload_to='documents/predict/burn/%Y/%m/%d')),
                ('predicted', models.BooleanField(default=False)),
                ('burn_result', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='demo.PredictResult')),
            ],
        ),
    ]
