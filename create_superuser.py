import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

try:
    # Cria ou atualiza o superuser
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@test.com',
            'is_superuser': True,
            'is_staff': True,
            'is_active': True
        }
    )
    if created:
        user.set_password('senha123')  # Isso criptografa automaticamente
        user.save()
        print("Superuser criado: admin/senha123")
    else:
        user.set_password('senha123')
        user.save()
        print("Senha do admin resetada: admin/senha123")
except Exception as e:
    print(f"Erro: {str(e)}")