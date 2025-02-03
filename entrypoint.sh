#!/bin/sh

# Run database migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Check if the superuser already exists
if [ "$(python manage.py shell -c 'from django.conf import settings; from django.apps import apps; User = apps.get_model(settings.AUTH_USER_MODEL); print(User.objects.filter(username="admin").exists())')" = "False" ]; then
    # Create a superuser with a predefined password
    echo "Creating superuser..."
    python manage.py shell -c 'from django.conf import settings; from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser("admin", "yash.garg@mobiloitte.com", "Admin@123", is_active=True, is_staff=True, is_superuser=True)'
fi

# Start the Django development server
echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8062
