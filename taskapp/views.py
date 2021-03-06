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
from .push import *

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
		overallScoreThisMonth = 0
		overallScoreLastMonth = 0
		userSetup.companyTasks = CompanyTask.get_open_for_user_setup(userSetup).order_by('title')
		userSetup.freeTasks = CompanyTask.get_open_for_company(company = userSetup.company).order_by('title')
		userSetup.users = UserSetup.get_rank_by_company(company = userSetup.company)
		for user in userSetup.users:
			user.score_this_month = user.monthly_score_delta(0)
			user.score_last_month = user.monthly_score_delta(1)
			overallScoreThisMonth += user.score_this_month
			overallScoreLastMonth += user.score_last_month
		for user in userSetup.users:
			if overallScoreThisMonth == 0:
				user.percent_score_this_month = 0.0
			else:
				user.percent_score_this_month = user.score_this_month / overallScoreThisMonth * 100
			if overallScoreLastMonth == 0:
				user.percent_score_last_month = 0.0
			else:
				user.percent_score_last_month = user.score_last_month / overallScoreLastMonth * 100
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
	history_item.user.push(request.user.username + " reverted: " + history_item.message) 
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
	dest_user_setup.push(src_user_setup.user.username + " modified your score by " + str(score) + ": " + message)
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
		overallScoreThisMonth = 0
		overallScoreLastMonth = 0

		item = {}
		item['score'] = user_setup.score
		item['companyId'] = user_setup.company.id
		item['userSetupId'] = user_setup.id
		companies.append(item)
		company_tasks = []
		for task in CompanyTask.get_open_for_company(user_setup.company).order_by('title'):
			company_tasks.append({
				'id': task.id,
				'title': task.title,
				'score': task.score,
				'penalty': default_on_none(task.penalty, 0),
				'regular': task.regular != None
			})
		user_tasks = []
		for task in CompanyTask.get_open_for_user_setup(user_setup).order_by('title'):
			user_tasks.append({
				'id': task.id,
				'title': task.title,
				'score': task.score,
				'penalty': default_on_none(task.penalty, 0),
				'regular': task.regular != None
			})
		history = []
		for history_item in user_setup.history(100):
			history.append({
				'score': history_item.score,
				'message': history_item.message,
				'created': history_item.created.strftime('%Y-%m-%d %H:%M')
				})
		user_ranks = []
		i = 0
		for user_setup in UserSetup.get_rank_by_company(company = user_setup.company):
			i += 1
			this_month_score = user_setup.monthly_score_delta(0)
			last_month_score = user_setup.monthly_score_delta(1)
			current_user_rank = {
				'userId': user_setup.user.id,
				'userSetupId': user_setup.id,
				'rank': i,
				'username': user_setup.user.username,
				'score': user_setup.score,
				'scoreThisMonth': user_setup.monthly_score_delta(0),
				'scoreLastMonth': user_setup.monthly_score_delta(1)
			}
			user_ranks.append(current_user_rank)
			if current_user_rank['userId'] == user.id:
				item['user'] = current_user_rank
			overallScoreThisMonth += this_month_score
			overallScoreLastMonth += last_month_score
		for user_rank in user_ranks:
			if overallScoreThisMonth == 0:
				user_rank['percentScoreThisMonth'] = 0
			else:
				user_rank['percentScoreThisMonth'] = user_rank['scoreThisMonth'] / overallScoreThisMonth
				
			if overallScoreLastMonth == 0:
				user_rank['percentScoreLastMonth'] = 0
			else:
				user_rank['percentScoreLastMonth'] = user_rank['scoreLastMonth'] / overallScoreLastMonth
		item['name'] = user_setup.company.name
		item['companyTasks'] = company_tasks
		item['userTasks'] = user_tasks
		item['history'] = history
		item['userRank'] = user_ranks
	result['companies'] = companies
	return JsonResponse(result)

def json_data_company(request, usersetup_id):
	user_setup = UserSetup.objects.get(id=usersetup_id)
	item = {}
	item['score'] = user_setup.score
	item['companyId'] = user_setup.company.id
	item['userSetupId'] = user_setup.id
	company_tasks = []
	for task in CompanyTask.get_open_for_company(user_setup.company).order_by('title'):
		company_tasks.append({
			'id': task.id,
			'title': task.title,
			'score': task.score,
			'penalty': default_on_none(task.penalty, 0),
			'regular': task.regular != None
		})
	user_tasks = []
	for task in CompanyTask.get_open_for_user_setup(user_setup).order_by('title'):
		user_tasks.append({
			'id': task.id,
			'title': task.title,
			'score': task.score,
			'penalty': default_on_none(task.penalty, 0),
			'regular': task.regular != None
		})
	history = []
	for history_item in user_setup.history(100):
		history.append({
			'score': history_item.score,
			'message': history_item.message,
			'created': history_item.created.strftime('%Y-%m-%d %H:%M')
			})
	user_rank = []
	i = 0
	for user_setup in UserSetup.get_rank_by_company(company = user_setup.company):
		i += 1
		user_rank.append({
			'rank': i,
			'username': user_setup.user.username,
			'score': user_setup.score
		})
	item['name'] = user_setup.company.name
	item['companyTasks'] = company_tasks
	item['userTasks'] = user_tasks
	item['history'] = history
	item['userRank'] = user_rank
	return JsonResponse(item)


def json_data_tasklist(request, company_id):
	company = Company.objects.get(id=company_id)
	result = {}
	tasks = []
	for task in CompanyTask.get_open_for_company(company).order_by('title'):
		tasks.append({
			'id': task.id,
			'title': task.title,
			'score': task.score,
			'penalty': default_on_none(task.penalty, 0),
			'regular': task.regular != None
		})
	result['tasks'] = tasks
	return JsonResponse(result)

def json_data_usersetup(request, usersetup_id):
	user_setup = UserSetup.objects.get(id=usersetup_id)
	result = {}
	tasks = []
	for task in CompanyTask.get_open_for_user_setup(user_setup).order_by('title'):
		tasks.append({
			'id': task.id,
			'title': task.title,
			'score': task.score,
			'penalty': default_on_none(task.penalty, 0),
			'regular': task.regular != None
		})
	result['tasks'] = tasks
	return JsonResponse(result)

def json_data_history(request, user_setup_id):
	user_setup = UserSetup.objects.get(id=user_setup_id)
	result = {}
	history = []
	for history_item in user_setup.history(100):
			history.append({
				'score': history_item.score,
				'message': history_item.message,
				'created': history_item.created.strftime('%Y-%m-%d %H:%M')
				})
	result['history'] = history
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

def json_edit_task(request, task_id):
	username = request.GET['username']
	password = request.GET['password']

	user = auth.authenticate(username = username, password = password)
	# TODO Check if user can edit the task
	if task_id <= 0:
		task = CompanyTask()
		company = Company.objects.get(id=int(request.GET['company']))
		task.company = company
	else:
		task = CompanyTask.objects.get(id = task_id)
	new_title = request.GET['title']
	new_score = float(request.GET['score'].replace(',', '.'))
	new_penalty = float(request.GET['penalty'].replace(',', '.'))
	new_regular_bool = request.GET['regular'] == 'True'
	if new_regular_bool == True:
		new_regular = datetime.timedelta(0)
	else:
		print("Regular is false")
		new_regular = None
	task.title = new_title
	task.score = new_score
	task.penalty = new_penalty
	task.regular = new_regular
	task.save()
	return JsonResponse({'success': True}) 

def json_modify_score(request, user_setup_id):
	username = request.GET['username']
	password = request.GET['password']
	user = auth.authenticate(username = username, password = password)

	if user == None:
		return JsonResponse({'success': False})

	message = request.GET['message']
	score_delta = float(request.GET['score-delta'])
	dest_user_setup = get_object_or_404(UserSetup.objects, id=user_setup_id)
	src_user_setup = get_object_or_404(UserSetup.objects, user = user, company = dest_user_setup.company)
	dest_user_setup.modify_score(score_delta, src_user_setup.user.username + " modification: " + message)
	dest_user_setup.push(username + " modified your score by " + str(score_delta) + ": " + message)
	return JsonResponse({'success': True})

def send_message(request, user_id):
	message = request.GET['message']
	user = get_object_or_404(User.objects, id=user_id)
	push(user, message)







