from django.db import models
from django.conf import settings

class Category(models.Model):
    """Görev kategorileri"""
    name = models.CharField(max_length=100, verbose_name='Kategori Adı')
    description = models.TextField(blank=True, null=True, verbose_name='Açıklama')
    color = models.CharField(max_length=7, default='#000000', verbose_name='Renk')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories', verbose_name='Kullanıcı', null=True, blank=True)
    is_default = models.BooleanField(default=False, verbose_name='Temel Kategori')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategoriler'
        ordering = ['name']

    def __str__(self):
        return self.name

class Task(models.Model):
    """Görev modeli"""
    STATUS_CHOICES = [
        ('todo', 'Yapılacak'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Düşük'),
        ('medium', 'Orta'),
        ('high', 'Yüksek'),
    ]

    title = models.CharField(max_length=200, verbose_name='Başlık')
    description = models.TextField(verbose_name='Açıklama')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='tasks', verbose_name='Kategori')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks', verbose_name='Atanan Kişi')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks', verbose_name='Oluşturan')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name='Durum')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='Öncelik')
    due_date = models.DateTimeField(verbose_name='Teslim Tarihi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Görev'
        verbose_name_plural = 'Görevler'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Group(models.Model):
    name = models.CharField(max_length=100, verbose_name='Grup Adı')
    description = models.TextField(blank=True, null=True, verbose_name='Açıklama')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_groups', verbose_name='Oluşturan')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Yönetici'),
        ('member', 'Üye'),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user} - {self.group} ({self.role})"

class GroupTask(models.Model):
    STATUS_CHOICES = [
        ('todo', 'Yapılacak'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Düşük'),
        ('medium', 'Orta'),
        ('high', 'Yüksek'),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200, verbose_name='Başlık')
    description = models.TextField(verbose_name='Açıklama', blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_tasks', verbose_name='Sorumlu')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name='Durum')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='Öncelik')
    due_date = models.DateTimeField(verbose_name='Teslim Tarihi', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.group.name})"

class GroupPost(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_posts')
    content = models.TextField(verbose_name='İçerik')
    image = models.ImageField(upload_to='group_posts/images/', null=True, blank=True, verbose_name='Görsel')
    file = models.FileField(upload_to='group_posts/files/', null=True, blank=True, verbose_name='Döküman')
    is_pinned = models.BooleanField(default=False, verbose_name='Sabitlendi mi?')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.group}"

class GroupComment(models.Model):
    post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_comments')
    content = models.TextField(verbose_name='Yorum')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.post}"
