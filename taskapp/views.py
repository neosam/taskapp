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
		userSetup.companyTasks = CompanyTask.get_open_for_user_setup(userSetup).order_by('title')
		userSetup.freeTasks = CompanyTask.get_open_for_company(company = userSetup.company).order_by('title')
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
	# TODO:  Security check if is allowed to edit the task
	task = get_object_or_404(CompanyTask.objects, id = task_id)
	if request.method == 'POST':
		form = TaskForm(request.POST, instance = task)
		if form.is_valid():
			form.save()
			return redirect('..')
	else:
		form = TaskForm(instance = task)
	return render(request, 'taskapp/task.html', {'form': form, 'action': str(task_id)})

@login_required(login_url="/accounts/login")
def new_task(request, company_id):
	company = get_object_or_404(Company.objects, id = company_id)
	task = CompanyTask(company = company)
	if request.method == 'POST':
		form = TaskForm(request.POST, instance = task)
		if form.is_valid():
			# TODO:  Check if user is allowed to add a task
			form.save()
			return redirect('..')
	else:
		form = TaskForm(instance = task)
	return render(request, 'taskapp/task.html', {'form': form, 'action': '../new-task/' + str(company_id)})

@login_required(login_url="/accounts/login")
def new_user_task(request, user_setup_id):
	user_setup = get_object_or_404(UserSetup.objects, id = user_setup_id)
	company = user_setup.company
	task = CompanyTask(company = company, assignment = user_setup)
	if request.method == 'POST':
		form = TaskForm(request.POST, instance = task)
		if form.is_valid():
			# TODO:  Check if user is allowed to add a task
			form.save()
			return redirect('../user-setup-details/' + str(user_setup.id))
	else:
		form = TaskForm(instance = task)
	return render(request, 'taskapp/task.html', {'form': form, 'action': '../new-user-task/' + str(user_setup_id)})

@login_required(login_url="/accounts/login")
def user_setup_details(request, user_setup_id):
	user_setup = get_object_or_404(UserSetup.objects, id=user_setup_id)
	user_setup.history_vals = user_setup.history(100)
	return render(request, 'taskapp/user-setup-details.html', {'user_setup': user_setup})

@login_required(login_url="/accounts/login")
def revert_history_item(request, history_id):
	# TODO: Check permissions
	history_item = get_object_or_404(UserScoreHistory.objects, id=history_id)
	history_item.user.modify_score(-history_item.score_delta, request.user.username + " reverted: " + history_item.message)
	return redirect('../user-setup-details/' + str(history_item.user.id))

def mod_score(request, user_setup_id):
	# TODO: Check permissions
	if request.method != 'POST':
		return redirect('../user-setup-details/' + str(dest_user_setup.id))
	score = int(request.POST['score'])
	message = request.POST['message']
	dest_user_setup = get_object_or_404(UserSetup.objects, id=user_setup_id)
	src_user_setup = get_object_or_404(UserSetup.objects, user = request.user, company = dest_user_setup.company)
	dest_user_setup.modify_score(score, src_user_setup.user.username + " modification: " + message)
	return redirect('../user-setup-details/' + str(dest_user_setup.id))


