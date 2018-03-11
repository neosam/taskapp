from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404

from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required(login_url="/accounts/login")
def index(request):
	user = request.user
	userSetups = UserSetup.objects.filter(user=user)
	for userSetup in userSetups:
		userSetup.companyTasks = CompanyTask.get_open_for_user_setup(userSetup)
		userSetup.freeTasks = CompanyTask.get_open_for_company(company = userSetup.company)
		userSetup.users = UserSetup.get_rank_by_company(company = userSetup.company)
		userSetup.history_vals = userSetup.history(10)
	return render(request, "taskapp/index.html", {'userSetups': userSetups})

@login_required(login_url="/accounts/login")
def complete(request, task_id):
	task = get_object_or_404(CompanyTask.objects, id=task_id)
	user = get_object_or_404(UserSetup, user=request.user, company = task.company)
	task.complete(user)
	return redirect('..')

@login_required(login_url="/accounts/login")
def edit_task(request, task_id):
	task = get_object_or_404(CompanyTask.objects, id = task_id)
	if request.method == 'POST':
		form = TaskForm(request.POST, instance = task)
		if form.is_valid():
			form.save()
			return redirect('..')
	else:
		form = TaskForm(instance = task)
	return render(request, 'taskapp/task.html', {'form': form})
