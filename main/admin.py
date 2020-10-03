from django.contrib import admin
<<<<<<< HEAD

# Register your models here.
=======
from .models import PatientData,BurnDocument,HandDocument
# Register your models here.


class PatientDataAdmin(admin.ModelAdmin):
    list_display = ["patient_id",'name','burn_type']

admin.site.register(PatientData,PatientDataAdmin)
admin.site.register(BurnDocument)
admin.site.register(HandDocument)
>>>>>>> e281625346f12ddae273a486a5ef4fea1ca65dda
