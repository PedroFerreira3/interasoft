from .settings import *

DEBUG = True
SECRET_KEY = 'chave-para-desenvolvimento'
ALLOWED_HOSTS = ['*']

# Desativa segurança HTTPS para desenvolvimento
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False