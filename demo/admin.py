from django.contrib import admin
from .models import PatientData,BurnDocument,HandDocument,PredictResult
# Register your models here.


class PatientDataAdmin(admin.ModelAdmin):
    list_display = ["patient_id",'name','burn_type']

admin.site.register(PatientData,PatientDataAdmin)
admin.site.register(BurnDocument)
admin.site.register(HandDocument)
admin.site.register(PredictResult)
