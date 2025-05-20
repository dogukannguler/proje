from django.db import models
from django.conf import settings

class Notification(models.Model):
    """Bildirim modeli"""
    NOTIFICATION_TYPES = [
        ('task_due', 'Görev Teslim Tarihi'),
        ('task_assigned', 'Görev Atandı'),
        ('task_updated', 'Görev Güncellendi'),
        ('task_completed', 'Görev Tamamlandı'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name='Kullanıcı')
    title = models.CharField(max_length=200, verbose_name='Başlık')
    message = models.TextField(verbose_name='Mesaj')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name='Bildirim Tipi')
    is_read = models.BooleanField(default=False, verbose_name='Okundu mu?')
    related_task = models.ForeignKey('task_manager.Task', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications', verbose_name='İlgili Görev')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bildirim'
        verbose_name_plural = 'Bildirimler'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"
