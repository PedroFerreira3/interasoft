"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import redirect
from cursos import views as cursos_views

#temporário
from django.contrib.auth import get_user_model
from django.http import HttpResponse

def create_admin(request):
    User = get_user_model()
    User.objects.create_superuser('admin', 'admin@test.com', 'senha123')
    return HttpResponse("Superuser criado: admin/senha123")

urlpatterns = [
    path('createadmin/', create_admin),  # Remova depois!
]
#temporário

def home(request):
    return HttpResponse("Bem-vindo à página inicial!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('cursos/', include('cursos.urls')),
    path('', lambda request: redirect('usuarios/login')),
    path('certificados/', include('certificados.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout/password urls
    path('api/', include('cursos.api_urls')),  # Todas APIs centralizadas

]
