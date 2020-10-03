from django.db import models

<<<<<<< HEAD
# Create your models here.
=======
    created = models.DateTimeField('Created Date',default=datetime.now())

    class Meta:
        # Gives the proper plural name for admin
        verbose_name_plural = "PatientData"

    def __str__(self):
        return self.patient_id

class BurnDocument(models.Model):
    burn_docfile = models.FileField(upload_to='documents/burn/%Y/%m/%d')
    def __str__(self):
        return self.burn_docfile.path

class HandDocument(models.Model):
    hand_docfile = models.FileField(upload_to='documents/hand/%Y/%m/%d')
    def __str__(self):
        return self.hand_docfile.path

    def __str__(self):
        return self.hand_docfile.path
>>>>>>> e281625346f12ddae273a486a5ef4fea1ca65dda
