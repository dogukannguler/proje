from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Task, Category, Group, GroupMembership, GroupTask, GroupPost, GroupComment
from .forms import TaskForm, CategoryForm, GroupPostForm
from notification_system.models import Notification
import os
from django.conf import settings
from django.core.files.base import File
from django.utils import timezone
from collections import Counter
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from zoneinfo import ZoneInfo

User = get_user_model()

def handle_avatar_choice(request, user):
    avatar_choice = request.POST.get('avatar_choice')
    if avatar_choice:
        # STATICFILES_DIRS'in ilk elemanını kullan (ana static klasörü)
        static_dir = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.BASE_DIR / 'static'
        avatar_path = os.path.join(static_dir, 'avatars', avatar_choice)
        
        # Eğer dosya bulunamazsa parent dizine bak
        if not os.path.exists(avatar_path):
            avatar_path = os.path.join(settings.BASE_DIR.parent, 'static', 'avatars', avatar_choice)
        
        if os.path.exists(avatar_path):
            with open(avatar_path, 'rb') as f:
                user.profile_picture.save(avatar_choice, File(f), save=True)

def home(request):
    if request.user.is_authenticated:
        tasks = Task.objects.filter(assigned_to=request.user).order_by('-created_at')[:5]
        categories = Category.objects.all()
        return render(request, 'task_manager/home.html', {
            'tasks': tasks,
            'categories': categories
        })
    return render(request, 'task_manager/home.html')

@login_required
def task_list(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    now = timezone.now()
    # Süresi geçen ve tamamlanmamış görevleri otomatik tamamlandı yap
    expired_tasks = tasks.filter(due_date__lt=now).exclude(status='completed')
    expired_tasks.update(status='completed')
    # Filtreleme işlemleri
    search_query = request.GET.get('q')
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    category_id = request.GET.get('category')
    if category_id:
        tasks = tasks.filter(category_id=category_id)
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    priority = request.GET.get('priority')
    if priority:
        tasks = tasks.filter(priority=priority)
    tasks = tasks.order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'task_manager/task_list.html', {
        'tasks': tasks,
        'categories': categories,
        'now': now,
    })

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.assigned_to = request.user  # Otomatik olarak mevcut kullanıcıya ata
            task.save()
            
            # Bildirim oluştur
            Notification.objects.create(
                user=task.assigned_to,
                title='Yeni Görev Oluşturuldu',
                message=f'"{task.title}" görevi oluşturuldu.',
                notification_type='task_created',
                related_task=task
            )
            
            messages.success(request, 'Görev başarıyla oluşturuldu!')
            return redirect('task_list')  # Başarılı olunca doğrudan görev listesine yönlendir
    else:
        form = TaskForm()
    categories = Category.objects.all()
    return render(request, 'task_manager/task_form.html', {
        'form': form,
        'title': 'Yeni Görev',
        'categories': categories
    })

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    return render(request, 'task_manager/task_detail.html', {'task': task})

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Görev başarıyla güncellendi!')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'task_manager/task_form.html', {'form': form, 'title': 'Görevi Düzenle'})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, assigned_to=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Görev başarıyla silindi!')
        return redirect('task_list')
    return render(request, 'task_manager/task_confirm_delete.html', {'task': task})

@login_required
def calendar_view(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    now = timezone.now()
    # Süresi geçen ve tamamlanmamış görevleri otomatik tamamlandı yap
    expired_tasks = tasks.filter(due_date__lt=now).exclude(status='completed')
    expired_tasks.update(status='completed')
    return render(request, 'task_manager/calendar.html', {'tasks': tasks, 'now': now})

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'task_manager/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kategori başarıyla oluşturuldu!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'task_manager/category_form.html', {'form': form, 'title': 'Yeni Kategori'})

@login_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    # Temel kategori ise sadece admin düzenleyebilsin
    if category.is_default:
        if not request.user.is_staff:
            messages.error(request, "Temel kategoriler sadece adminler tarafından düzenlenebilir.")
            return redirect('category_list')
    else:
        # Temel olmayan kategorilerde sadece sahibi veya admin düzenleyebilsin
        if category.user and category.user != request.user and not request.user.is_staff:
            messages.error(request, "Bu kategoriyi sadece ekleyen kullanıcı veya admin düzenleyebilir.")
            return redirect('category_list')
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kategori başarıyla güncellendi!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'task_manager/category_form.html', {'form': form, 'title': 'Kategoriyi Düzenle'})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.is_default and not request.user.is_staff:
        messages.error(request, "Bu kategori sadece adminler tarafından silinebilir.")
        return redirect('category_list')
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Kategori başarıyla silindi!')
        return redirect('category_list')
    return render(request, 'task_manager/category_confirm_delete.html', {'category': category})

@login_required
def statistics_view(request):
    tasks = Task.objects.filter(assigned_to=request.user)
    total = tasks.count()
    completed = tasks.filter(status='completed').count()
    in_progress = tasks.filter(status='in_progress').count()
    todo = tasks.filter(status='todo').count()
    now = timezone.now()
    overdue = tasks.filter(due_date__lt=now, status__in=['todo', 'in_progress']).count()
    # Kategoriye göre dağılım
    category_counter = Counter(tasks.values_list('category__name', flat=True))
    category_labels = list(category_counter.keys())
    category_values = list(category_counter.values())
    # Duruma göre dağılım
    status_counter = Counter(tasks.values_list('status', flat=True))
    status_labels = list(status_counter.keys())
    status_values = list(status_counter.values())
    return render(request, 'task_manager/statistics.html', {
        'total': total,
        'completed': completed,
        'in_progress': in_progress,
        'todo': todo,
        'overdue': overdue,
        'category_labels': category_labels,
        'category_values': category_values,
        'status_labels': status_labels,
        'status_values': status_values,
    })

@require_POST
@login_required
def update_task_datetime(request):
    import json
    data = json.loads(request.body)
    task_id = data.get('task_id')
    new_date = data.get('date')  # 'YYYY-MM-DD'
    new_time = data.get('time')  # 'HH:MM'
    try:
        task = Task.objects.get(pk=task_id, assigned_to=request.user)
        from datetime import datetime
        from django.utils import timezone
        dt_str = f"{new_date} {new_time}"
        dt = timezone.make_aware(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"))
        task.due_date = dt
        # Eğer görev tamamlandıysa ve yeni tarih gelecekteyse, durumu 'todo' yap
        if task.status == 'completed' and dt > timezone.now():
            task.status = 'todo'
        task.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def group_list(request):
    memberships = GroupMembership.objects.filter(user=request.user)
    groups = [m.group for m in memberships]
    return render(request, 'task_manager/group_list.html', {'groups': groups})

@login_required
def group_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            group = Group.objects.create(name=name, description=description, created_by=request.user)
            GroupMembership.objects.create(group=group, user=request.user, role='admin')
            return redirect('group_detail', group_id=group.id)
    return render(request, 'task_manager/group_create.html')

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Erişim kontrolü: sadece üye görebilir
    members = GroupMembership.objects.filter(group=group)
    is_member = members.filter(user=request.user).exists()
    is_admin = members.filter(user=request.user, role='admin').exists()
    if not is_member:
        return HttpResponseForbidden('Bu gruba erişim izniniz yok.')

    post_form = GroupPostForm()
    # Sabitleme/Çıkarma işlemi
    if request.method == 'POST' and 'pin_post_id' in request.POST:
        pin_post_id = request.POST.get('pin_post_id')
        post_to_pin = get_object_or_404(GroupPost, id=pin_post_id, group=group)
        # Sadece admin veya paylaşım sahibi sabitleyebilir
        if is_admin or post_to_pin.user == request.user:
            # Eğer zaten sabitli ise kaldır, değilse sabitle
            post_to_pin.is_pinned = not post_to_pin.is_pinned
            post_to_pin.save()
            messages.success(request, 'Paylaşım sabitleme durumu değiştirildi.')
        return redirect(f'{reverse("group_detail", args=[group.id])}?tab=posts')
    # Görev ekleme ve paylaşım ekleme
    if request.method == 'POST' and 'add_task' in request.POST:
        title = request.POST.get('task_title')
        description = request.POST.get('task_description')
        assigned_to_id = request.POST.get('task_assigned_to')
        assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
        if title:
            GroupTask.objects.create(
                group=group,
                title=title,
                description=description or '',
                assigned_to=assigned_to,
                status='todo',
                priority='medium',
            )
            messages.success(request, 'Grup görevi eklendi.')
            return redirect(f'{reverse("group_detail", args=[group.id])}?tab=tasks')
    elif request.method == 'POST' and 'add_post' in request.POST:
        post_form = GroupPostForm(request.POST, request.FILES)
        if post_form.is_valid():
            new_post = post_form.save(commit=False)
            new_post.group = group
            new_post.user = request.user
            new_post.save()
            messages.success(request, 'Paylaşım eklendi.')
            return redirect(f'{reverse("group_detail", args=[group.id])}?tab=posts')
    elif request.method == 'POST' and 'add_comment' in request.POST:
        post_id = request.POST.get('comment_post_id')
        comment_content = request.POST.get('comment_content')
        if post_id and comment_content:
            post = get_object_or_404(GroupPost, id=post_id, group=group)
            GroupComment.objects.create(post=post, user=request.user, content=comment_content)
            messages.success(request, 'Yorum eklendi.')
            return redirect(f'{reverse("group_detail", args=[group.id])}?tab=posts')

    tasks = GroupTask.objects.filter(group=group)
    posts = GroupPost.objects.filter(group=group).order_by('-is_pinned', '-created_at')
    return render(request, 'task_manager/group_detail.html', {
        'group': group,
        'members': members,
        'tasks': tasks,
        'posts': posts,
        'is_member': is_member,
        'is_admin': is_admin,
        'active_tab': request.GET.get('tab', 'tasks'),
        'post_form': post_form,
    })

@login_required
def group_add_member(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Sadece adminler üye ekleyebilir
    if not GroupMembership.objects.filter(group=group, user=request.user, role='admin').exists():
        return HttpResponseForbidden('Sadece grup yöneticileri üye ekleyebilir.')
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        User = get_user_model()
        user = User.objects.filter(Q(username=username_or_email) | Q(email=username_or_email)).first()
        if not user:
            messages.error(request, 'Kullanıcı bulunamadı.')
        elif GroupMembership.objects.filter(group=group, user=user).exists():
            messages.warning(request, 'Bu kullanıcı zaten grup üyesi.')
        else:
            GroupMembership.objects.create(group=group, user=user, role='member')
            messages.success(request, f'{user.get_full_name() or user.username} gruba eklendi.')
        return redirect(reverse('group_detail', args=[group.id]))
    return redirect(reverse('group_detail', args=[group.id]))

@login_required
def group_task_edit(request, group_id, task_id):
    group = get_object_or_404(Group, id=group_id)
    task = get_object_or_404(GroupTask, id=task_id, group=group)
    # Sadece grup üyesi düzenleyebilir
    if not GroupMembership.objects.filter(group=group, user=request.user).exists():
        return HttpResponseForbidden('Bu grupta düzenleme yetkiniz yok.')
    if request.method == 'POST':
        task.title = request.POST.get('title')
        task.description = request.POST.get('description')
        assigned_to_id = request.POST.get('assigned_to')
        task.assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
        task.status = request.POST.get('status')
        due_date = request.POST.get('due_date')
        if due_date:
            dt = parse_datetime(due_date)
            if dt and not dt.tzinfo:
                dt = dt.replace(tzinfo=ZoneInfo('UTC'))
            task.due_date = dt
        task.save()
        messages.success(request, 'Grup görevi güncellendi.')
        return redirect('group_detail', group_id=group.id)
    return redirect('group_detail', group_id=group.id)

@login_required
def group_task_delete(request, group_id, task_id):
    group = get_object_or_404(Group, id=group_id)
    task = get_object_or_404(GroupTask, id=task_id, group=group)
    # Sadece grup üyesi silebilir
    if not GroupMembership.objects.filter(group=group, user=request.user).exists():
        return HttpResponseForbidden('Bu grupta silme yetkiniz yok.')
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Grup görevi silindi.')
        return redirect('group_detail', group_id=group.id)
    return redirect('group_detail', group_id=group.id)

@login_required
def group_post_edit(request, group_id, post_id):
    group = get_object_or_404(Group, id=group_id)
    post = get_object_or_404(GroupPost, id=post_id, group=group)
    if post.user != request.user:
        return HttpResponseForbidden('Sadece kendi paylaşımınızı düzenleyebilirsiniz.')
    if request.method == 'POST':
        content = request.POST.get('content')
        tab = request.POST.get('tab', 'posts')
        if content:
            post.content = content
            post.save()
            messages.success(request, 'Paylaşım güncellendi.')
        return redirect(f'{reverse("group_detail", args=[group.id])}?tab={tab}')
    return render(request, 'task_manager/group_post_edit.html', {'post': post, 'group': group})

@login_required
def group_post_delete(request, group_id, post_id):
    group = get_object_or_404(Group, id=group_id)
    post = get_object_or_404(GroupPost, id=post_id, group=group)
    if post.user != request.user:
        return HttpResponseForbidden('Sadece kendi paylaşımınızı silebilirsiniz.')
    if request.method == 'POST':
        tab = request.POST.get('tab', 'posts')
        post.delete()
        messages.success(request, 'Paylaşım silindi.')
        return redirect(f'{reverse("group_detail", args=[group.id])}?tab={tab}')
    return render(request, 'task_manager/group_post_delete.html', {'post': post, 'group': group})

@login_required
def group_comment_edit(request, group_id, comment_id):
    group = get_object_or_404(Group, id=group_id)
    comment = get_object_or_404(GroupComment, id=comment_id, post__group=group)
    if comment.user != request.user:
        return HttpResponseForbidden('Sadece kendi yorumunuzu düzenleyebilirsiniz.')
    if request.method == 'POST':
        content = request.POST.get('content')
        tab = request.POST.get('tab', 'posts')
        if content:
            comment.content = content
            comment.save()
            messages.success(request, 'Yorum güncellendi.')
        return redirect(f'{reverse("group_detail", args=[group.id])}?tab={tab}')
    return render(request, 'task_manager/group_comment_edit.html', {'comment': comment, 'group': group})

@login_required
def group_comment_delete(request, group_id, comment_id):
    group = get_object_or_404(Group, id=group_id)
    comment = get_object_or_404(GroupComment, id=comment_id, post__group=group)
    if comment.user != request.user:
        return HttpResponseForbidden('Sadece kendi yorumunuzu silebilirsiniz.')
    if request.method == 'POST':
        tab = request.POST.get('tab', 'posts')
        comment.delete()
        messages.success(request, 'Yorum silindi.')
        return redirect(f'{reverse("group_detail", args=[group.id])}?tab={tab}')
    return render(request, 'task_manager/group_comment_delete.html', {'comment': comment, 'group': group})

@login_required
def leave_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()
    if not membership:
        return HttpResponseForbidden('Bu grupta üye değilsiniz.')
    if request.method == 'POST':
        membership.delete()
        messages.success(request, f'{group.name} grubundan ayrıldınız.')
        return redirect('group_list')
    return redirect('group_detail', group_id=group.id)

@login_required
def group_calendar(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    members = GroupMembership.objects.filter(group=group)
    is_member = members.filter(user=request.user).exists()
    if not is_member:
        return HttpResponseForbidden('Bu gruba erişim izniniz yok.')
    tasks = GroupTask.objects.filter(group=group)
    return render(request, 'task_manager/group_calendar.html', {
        'group': group,
        'members': members,
        'tasks': tasks,
    })

def contact(request):
    return render(request, 'task_manager/contact.html')

def faq(request):
    return render(request, 'task_manager/faq.html')

def help_page(request):
    return render(request, 'task_manager/help.html')
