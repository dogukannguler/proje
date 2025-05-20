from django.core.management.base import BaseCommand
from django.utils import timezone
from task_manager.models import Task
from notification_system.models import Notification
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Yaklaşan görevler için kullanıcılara bildirim gönderir.'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        soon = now + timedelta(hours=1)  # 1 saat içinde teslim tarihi olanlar
        tasks = Task.objects.filter(due_date__gte=now, due_date__lte=soon, status__in=['todo', 'in_progress'])
        for task in tasks:
            # Aynı bildirim tekrar oluşmasın diye kontrol
            if not Notification.objects.filter(user=task.assigned_to, related_task=task, notification_type='reminder', created_at__date=now.date()).exists():
                Notification.objects.create(
                    user=task.assigned_to,
                    title='Yaklaşan Görev!',
                    message=f'"{task.title}" görevinin teslim süresi yaklaşıyor.',
                    notification_type='reminder',
                    related_task=task
                )
                self.stdout.write(self.style.SUCCESS(f'Bildirim gönderildi: {task.title} - {task.assigned_to}')) 