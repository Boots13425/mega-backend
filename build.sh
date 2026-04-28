#!/usr/bin/env bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating admin user..."
python manage.py shell <<'PY'
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

user, created = User.objects.get_or_create(
    username="megaglow",
    defaults={"is_staff": True, "is_superuser": False, "is_active": True},
)
user.is_staff = True
user.is_superuser = False
user.is_active = True
user.set_password("mega123glow")
user.save()

Token.objects.get_or_create(user=user)
print("Admin user is ready")
PY

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "✓ Build completed successfully"