from django.db import models
from datetime import datetime
# Create your models here.


class PatientData(models.Model):
    SEX_CHOICES = (
        ('f', 'Female',),
        ('m', 'Male',),
        ('u', 'Unsure',),
    )

    burn_choice = (
        ('s','Scald'),
        ('g','Grease'),
        ('n','Contact'),
        ('f','Flame'),
        ('c','Chemical'),
        ('e','Electric'),
        ('o','Other'),
    )
    name = models.CharField(max_length=200)
    patient_id = models.CharField(max_length=200)
    age = models.IntegerField(default=0)
    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES,)
    height = models.FloatField()
    weight = models.FloatField()
    burn_type =  models.CharField(
        max_length=1,
        choices=burn_choice,)
    comments = models.TextField()

    created = models.DateTimeField('Created Date',default=datetime.now())

    class Meta:
        # Gives the proper plural name for admin
        verbose_name_plural = "PatientData"

    def __str__(self):
        return self.patient_id


class PredictResult(models.Model):
    predicted_time = models.DateTimeField(default=datetime.now, blank=True)
    result_code = models.CharField(default='',blank=True,max_length=1024)
    predict_tbsa_ai = models.FloatField(default=0)
    ai_after_eight_hours = models.FloatField(default=0)
    ai_after_sixteen_hours = models.FloatField(default=0)
    manual_after_eight_hours = models.FloatField(default=0)
    manual_after_sixteen_hours = models.FloatField(default=0)
    def __str__(self):
        return str(self.predicted_time)


class HandDocument(models.Model):
    hand_docfile_resized = models.ImageField(upload_to='documents/hand',blank=True)
    hand_docfile_ori = models.ImageField(upload_to='documents/hand',blank=True)
    hand_predict_docfile = models.ImageField(upload_to='documents/predict/hand',blank=True)
    file_location = models.CharField(default="",max_length=2048)
    predicted = models.BooleanField(default=False)
    process_predict = models.BooleanField(default=False)
    hand_pixel = models.IntegerField(default=0)

    hand_result = models.OneToOneField(PredictResult, on_delete=models.SET_NULL,blank=True,null=True)
    def __str__(self):
        return str(self.hand_docfile_resized.path)

class BurnDocument(models.Model):
    burn_docfile_resized = models.ImageField(upload_to='documents/burn',blank=True)
    burn_docfile_ori = models.ImageField(upload_to='documents/burn',blank=True)
    file_location = models.CharField(default="",max_length=2048)
    burn_predict_docfile = models.ImageField(upload_to='documents/predict/burn',blank=True)
    predicted = models.BooleanField(default=False)
    process_predict = models.BooleanField(default=False)
    burn_pixel = models.IntegerField(default=0)
    burn_result = models.ForeignKey(PredictResult, on_delete=models.SET_NULL,blank=True,null=True)
    user_calculated_tbsa = models.FloatField(blank=True,null=True,default=0.0)
    def __str__(self):
        return str(self.burn_docfile_resized.path)
