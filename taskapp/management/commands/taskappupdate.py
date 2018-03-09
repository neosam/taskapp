from django.core.management.base import BaseCommand, CommandError
from taskapp.models import *
from datetime import datetime

class Command(BaseCommand):
    help = 'Lowers positive score'

    def handle(self, *args, **options):
        score_lowering = 0.9

        # Reduce positive score
        for user_setup in UserSetup.objects.filter(score__gt = 0):
            user_setup.modify_score(-user_setup.score * 0.1, "Daily reduction")

        # Handle unfinished tasks
        for task in CompanyTask.objects.exclude(deadline = None, assignment = None).filter(deadline__lt = datetime.now()):
            task.assignment.modify_score(-task.penalty, "Deadline missed for " + task.title)

