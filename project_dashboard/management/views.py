from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from functools import wraps

CustomUser = get_user_model()

def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access the management dashboard.')
            return redirect('management:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_staff:
                login(request, user)
                return redirect('management:dashboard')
            else:
                messages.error(request, 'You do not have permission to access the management dashboard.')
    else:
        form = AuthenticationForm()
    return render(request, 'management/login.html', {'form': form})

@login_required
@staff_required
def dashboard(request):
    blockchain_users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'management/dashboard.html', {'blockchain_users': blockchain_users})

@login_required
@staff_required
def manage_users(request):
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'management/users.html', {'users': users})

@login_required
@staff_required
def add_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('management:users')
    else:
        form = UserCreationForm()
    return render(request, 'management/add_user.html', {'form': form})

@login_required
@staff_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserCreationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully.')
            return redirect('management:users')
    else:
        form = UserCreationForm(instance=user)
    return render(request, 'management/edit_user.html', {'form': form, 'user': user})

@require_POST
@login_required
@staff_required
def delete_user(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        user.delete()
        return JsonResponse({'success': True})
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@staff_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('management:login') 