import os
import django
from django.conf import settings

""" This file is a utility file to allow my unit tests to talk to Django or the database"""

## Tells Django to use the settings from calculator/settings.py which contains my database config, installed apps, etc
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calculator.settings')

## Initialize Django with the above settings
django.setup()
