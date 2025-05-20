from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification
from django.http import JsonResponse

# Create your views here.

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notification_system/notification_list.html', {'notifications': notifications})

@login_required
def mark_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, 'Bildirim okundu olarak işaretlendi.')
    return redirect('notifications')

@login_required
def mark_all_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'Tüm bildirimler okundu olarak işaretlendi.')
    return redirect('notifications')

@login_required
def new_notification(request):
    notification = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at').first()
    if notification:
        return JsonResponse({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.strftime('%d.%m.%Y %H:%M'),
        })
    return JsonResponse({}, status=204)
