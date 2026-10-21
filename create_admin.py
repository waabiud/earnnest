import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "YOUR_PROJECT.settings"
)
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = "abiud"
email = "wwamalwa@gmail.com"
password = os.environ.get("ADMIN_PASSWORD")

if not password:
    raise ValueError("ADMIN_PASSWORD is not configured")

user = User.objects.filter(username=username).first()

if user is None:
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
    )
    print("Superuser created successfully.")
else:
    user.email = email
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print("Existing account updated successfully.")

print("Username:", user.get_username())
print("Active:", user.is_active)
print("Staff:", user.is_staff)
print("Superuser:", user.is_superuser)
