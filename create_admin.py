import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "YOUR_PROJECT.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = "abiud"
email = "email@example.com"
password = os.environ.get("ADMIN_PASSWORD")

if not password:
    raise ValueError("ADMIN_PASSWORD is not configured")

if User.objects.filter(username=username).exists():
    print("User already exists")
else:
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
    )
    print("Superuser created successfully")
