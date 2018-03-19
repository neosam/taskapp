from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.core import serializers
from django.contrib.auth.models import User

from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib import auth

import datetime

def default_on_none(value, default_value):
	if value == None:
		return default_value
	else:
		return value

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
		userSetup.all_user_history = userSetup.company.all_user_history(datetime.timedelta(7))
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

def logout(request):
	auth.logout(request)
	return redirect('./')

def json_data(request):
	username = request.GET['username']
	password = request.GET['password']
	user = auth.authenticate(username = username, password = password)

	user_setups = UserSetup.objects.filter(user=user)
	result = {}
	companies = []
	for user_setup in user_setups:
		item = {}
		item['score'] = user_setup.score
		companies.append(item)
		company_tasks = []
		for task in CompanyTask.get_open_for_company(user_setup.company):
			company_tasks.append({
				'id': task.id,
				'title': task.title,
				'score': task.score,
				'penalty': default_on_none(task.penalty, 0)
			})
		user_tasks = []
		for task in CompanyTask.get_open_for_user_setup(user_setup):
			user_tasks.append({
				'id': task.id,
				'title': task.title,
				'score': task.score,
				'penalty': default_on_none(task.penalty, 0)
			})
		history = []
		for history_item in user_setup.history(100):
			history.append({
				'score': history_item.score,
				'message': history_item.message,
				'created': history_item.created.strftime('%Y-%m-%d %H:%M')
				})
		item['name'] = user_setup.company.name
		item['companyTasks'] = company_tasks
		item['userTasks'] = user_tasks
		item['history'] = history
	result['companies'] = companies
	return JsonResponse(result)

def json_login(request):
	username = request.GET['username']
	password = request.GET['password']

	user = auth.authenticate(username = username, password = password)
	if user == None:
		return JsonResponse({
			'success': False,
			'username': username,
			'userId': -1
		})
	else:
		return JsonResponse({
			'success': True,
			'username': username,
			'userId': user.id
		})

def json_complete_task(request, task_id):
	username = request.GET['username']
	password = request.GET['password']

	user = auth.authenticate(username = username, password = password)
	task = CompanyTask.objects.get(id = task_id)
	user_setup = UserSetup.objects.get(user = user, company = task.company)
	task.complete(user_setup)
	return JsonResponse({'success': True})

	




