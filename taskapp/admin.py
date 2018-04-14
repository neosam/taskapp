from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Company)
admin.site.register(CompanyTask)
admin.site.register(UserSetup)
admin.site.register(CompanyRule)
admin.site.register(UserScoreHistory)
admin.site.register(IosPush)
