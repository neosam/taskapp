from django import forms

from .models import *

class TaskForm(forms.ModelForm):
	class Meta:
		model = CompanyTask
		fields = ['title', 'score', 'penalty', 'deadline', 'regular']
