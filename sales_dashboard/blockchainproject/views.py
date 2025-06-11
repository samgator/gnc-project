from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth import login

def index(request):
    return render(request, 'blockchainproject/index.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.wallet_address = request.POST.get('metamask_wallet', '')
            user.save()
            login(request, user)
            return redirect('/blockchainproject/')
    else:
        form = CustomUserCreationForm()
    return render(request, 'blockchainproject/register.html', {'form': form})