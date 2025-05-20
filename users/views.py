from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.files import File
from django.conf import settings
import os
from .forms import CustomUserCreationForm, ProfileUpdateForm

# Create your views here.

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

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            
            # Eğer özel profil resmi yüklenmemişse ve avatar seçilmişse
            if not user.profile_picture and 'avatar_choice' in request.POST:
                handle_avatar_choice(request, user)
                
            login(request, user)
            messages.success(request, 'Hesabınız başarıyla oluşturuldu!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'users/profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Eğer yeni bir profil resmi yüklenmemişse ve avatar seçilmişse
            if not request.FILES.get('profile_picture') and 'avatar_choice' in request.POST:
                # Mevcut profil resmini temizle
                if user.profile_picture:
                    user.profile_picture.delete(save=False)
                handle_avatar_choice(request, user)
            else:
                user.save()
            
            new_password = form.cleaned_data.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Şifreniz başarıyla güncellendi! Lütfen tekrar giriş yapın.')
                return redirect('login')
                
            messages.success(request, 'Profiliniz başarıyla güncellendi!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})
