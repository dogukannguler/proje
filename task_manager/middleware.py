from django.utils import timezone
from task_manager.models import Task
from notification_system.models import Notification

class TaskDueNotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response:
            return response
        return self.get_response(request)

    def process_request(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            due_tasks = Task.objects.filter(
                assigned_to=request.user,
                due_date__lte=now,
                status__in=['todo', 'in_progress']
            )
            for task in due_tasks:
                # Aynı gün içinde aynı görev için tekrar bildirim oluşturma
                if not Notification.objects.filter(user=request.user, related_task=task, notification_type='task_due', created_at__date=now.date()).exists():
                    Notification.objects.create(
                        user=request.user,
                        title='Görev Zamanı Geldi!',
                        message=f'"{task.title}" görevinin zamanı geldi!',
                        notification_type='task_due',
                        related_task=task
                    )
        return None 