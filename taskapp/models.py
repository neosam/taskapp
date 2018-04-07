from django.db import models
from django.contrib.auth.models import User
import datetime
from django.db.models import Sum

# Create your models here.
class CompanyTask(models.Model):
	title = models.CharField(max_length=1000)
	created = models.DateTimeField(auto_now = True)
	deadline = models.DateTimeField(null = True, blank = True)
	regular = models.DurationField(null = True, blank = True)
	penalty = models.FloatField(null = True, blank = True)
	score = models.FloatField()
	company = models.ForeignKey('Company', on_delete = models.CASCADE)
	finished = models.BooleanField(default=False)
	assignment = models.ForeignKey('UserSetup', on_delete = models.CASCADE, null = True, blank = True)
	def __str__(self):
		return self.title + " @ " + self.company.name

	def complete(self, userSetup):
		# Check if someone else did the work
		if self.penalty != None and self.assignment != None and userSetup.id != self.assignment.id:
			self.assignment.modify_score(-self.penalty, "Task " + self.title + " compelted by " + userSetup.user.username)
		# Assign new deadline on regular tasks
		if self.regular != None and self.regular.total_seconds() > 0:
				self.deadline = datetime.datetime.now() + self.regular
		if self.regular == None:
			self.finished = True
		# Add score to user who completed the task
		userSetup.modify_score(self.score, "Completed task: " + self.title)
		self.save()

	def get_open_tasks():
		return CompanyTask.objects.filter(finished = False)
	def get_open_for_user_setup(user_setup):
		return CompanyTask.get_open_tasks().filter(assignment = user_setup)
	def get_open_for_user(user):
		userSetup = UserSetup.objects.get(user = user)
		return CompanyTask.get_open_tasks().filter(assignment = userSetup)
	def get_open_for_company(company):
		return CompanyTask.get_open_tasks().filter(company = company, assignment = None)




class CompanyRule(models.Model):
	title = models.CharField(max_length=1000)
	created = models.DateTimeField(auto_now = True)
	score = models.FloatField()
	company = models.ForeignKey('Company', on_delete = models.CASCADE)
	def __str__(self):
		return self.title + " @ " + self.company.name

class Company(models.Model):
    name = models.CharField(max_length=1000)
    def __str__(self):
    	return self.name

    def all_user_history(self, duration):
    	user_setups = UserSetup.objects.filter(company = self)
    	for user_setup in user_setups:
    		user_setup.history_vals = user_setup.history_for_duration(duration)
    	return user_setups
        

class UserSetup(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    company = models.ForeignKey('Company', on_delete = models.CASCADE)
    score = models.FloatField(default = 0)
    def __str__(self):
    	return self.user.username + " @ " + self.company.name

    def modify_score(self, score_delta, message):
    	self.score += score_delta
    	newUserScore = UserScoreHistory(
    			message = message,
    			user = self,
    			score = self.score,
    			score_delta = score_delta)
    	newUserScore.save()
    	self.save()

    def history(self, amount):
    	return UserScoreHistory.objects.filter(user = self).order_by('-created')[0:amount]

    def history_for_duration(self, duration):
    	return UserScoreHistory.objects.filter(user = self).filter(created__gt = datetime.datetime.now() - duration).order_by('-created')

    def get_rank_by_company(company):
    	return UserSetup.objects.filter(company = company).order_by('-score')

    def monthly_score(self, year, month):
    	begin = datetime.datetime(year, month, 1)
    	if month == 12:
    		month = 0
    		year += 1
    	end = datetime.datetime(year, month + 1, 1) - datetime.timedelta(1)
    	score = UserScoreHistory.objects.filter(user = self).filter(created__gt = begin, created__lt = end).exclude(message="Daily reduction").aggregate(Sum("score_delta"))['score_delta__sum']
    	if score == None:
    		score = 0
    	return score

    def monthly_score_delta(self, delta):
    	today = datetime.datetime.now()
    	year = today.year
    	month = today.month
    	month -= delta
    	while month < 1:
    		year -= 1
    		month += 12
    	return self.monthly_score(year, month)



class UserScoreHistory(models.Model):
	user = models.ForeignKey(UserSetup, on_delete = models.CASCADE)
	score = models.FloatField()
	score_delta = models.FloatField()
	message = models.CharField(max_length = 1000)
	created = models.DateTimeField(auto_now = True)
	def __str__(self):
		return str(self.user) + ": " + self.message[0:80] + " - (" + str(self.score) + ", " + str(self.score_delta) + ")"




