from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm, TokenTransferForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .web3_config import get_token_balance, send_tokens, TOKEN_CONTRACT_ADDRESS
from web3 import Web3

def index(request):
    return render(request, 'blockchainproject/index.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blockchainproject:index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'blockchainproject/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('blockchainproject:index')
    else:
        form = AuthenticationForm()
    return render(request, 'blockchainproject/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('blockchainproject:index')

@login_required
def get_balance(request):
    balance, error = get_token_balance(request.user.wallet_address)
    if error:
        return JsonResponse({'error': error})
    return JsonResponse({'balance': balance})

@login_required
def transfer(request):
    return render(request, 'blockchainproject/transfer.html', {
        'token_contract_address': TOKEN_CONTRACT_ADDRESS
    })