"""
Authentication views for RAG system
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib import messages
import json


class LoginView(View):
    """User login view"""
    
    def get(self, request):
        """Display login form"""
        if request.user.is_authenticated:
            return redirect('/cases/rag/')
        return render(request, 'auth/login.html')
    
    def post(self, request):
        """Process login"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            username = data.get('username', '')
            password = data.get('password', '')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': True,
                        'message': 'Login successful',
                        'redirect': '/cases/rag/'
                    })
                messages.success(request, 'Login successful!')
                return redirect('/cases/rag/')
            else:
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid username or password'
                    }, status=401)
                messages.error(request, 'Invalid username or password')
                return render(request, 'auth/login.html')
                
        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
            messages.error(request, f'Login error: {str(e)}')
            return render(request, 'auth/login.html')


class LogoutView(View):
    """User logout view"""
    
    def post(self, request):
        """Process logout"""
        logout(request)
        if request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Logout successful'
            })
        messages.success(request, 'You have been logged out')
        return redirect('/auth/login/')
    
    def get(self, request):
        """Display logout confirmation"""
        logout(request)
        messages.success(request, 'You have been logged out')
        return redirect('/auth/login/')


class RegisterView(View):
    """User registration view"""
    
    def get(self, request):
        """Display registration form"""
        if request.user.is_authenticated:
            return redirect('/cases/rag/')
        return render(request, 'auth/register.html')
    
    def post(self, request):
        """Process registration"""
        try:
            from django.contrib.auth.models import User
            
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            username = data.get('username', '')
            email = data.get('email', '')
            password = data.get('password', '')
            password_confirm = data.get('password_confirm', '')
            
            if not username or not password:
                error_msg = 'Username and password are required'
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                return render(request, 'auth/register.html')
            
            if password != password_confirm:
                error_msg = 'Passwords do not match'
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                return render(request, 'auth/register.html')
            
            if User.objects.filter(username=username).exists():
                error_msg = 'Username already exists'
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg}, status=400)
                messages.error(request, error_msg)
                return render(request, 'auth/register.html')
            
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': 'Registration successful',
                    'redirect': '/cases/rag/'
                })
            messages.success(request, 'Registration successful!')
            return redirect('/cases/rag/')
            
        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f'Registration error: {str(e)}')
            return render(request, 'auth/register.html')


class ProfileView(View):
    """User profile view"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Display user profile"""
        return render(request, 'auth/profile.html', {
            'user': request.user
        })
    
    @method_decorator(login_required)
    def post(self, request):
        """Update user profile"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            user = request.user
            
            email = data.get('email', user.email)
            first_name = data.get('first_name', user.first_name)
            last_name = data.get('last_name', user.last_name)
            
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': 'Profile updated successfully'
                })
            messages.success(request, 'Profile updated successfully')
            return render(request, 'auth/profile.html', {'user': user})
            
        except Exception as e:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f'Update error: {str(e)}')
            return render(request, 'auth/profile.html', {'user': request.user})


@require_GET
def check_auth(request):
    """Check if user is authenticated"""
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None
    })