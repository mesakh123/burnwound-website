from django.contrib import admin
from .models import PatientData,BurnDocument,HandDocument,PredictResult
# Register your models here.


class PatientDataAdmin(admin.ModelAdmin):
    list_display = ["patient_id",'updated','name','burn_type']
    readonly_fields = ('created','updated')
    search_fields = ('patient_id','name',)
class PredictResultAdmin(admin.ModelAdmin):
    search_fields = ('result_code', )
    readonly_fields = ('predicted_time',)
admin.site.register(PatientData,PatientDataAdmin)
admin.site.register(BurnDocument)
admin.site.register(HandDocument)
admin.site.register(PredictResult,PredictResultAdmin)
