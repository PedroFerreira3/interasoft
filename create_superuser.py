import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

# Verifica se o superuser já existe
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password=os.getenv('Estagio&123')  # Defina esta variável no Render
    )
    print("Superuser criado com sucesso!")
else:
    print("Superuser já existe")