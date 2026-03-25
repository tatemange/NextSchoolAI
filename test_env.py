import os
import django
import sys

# Setup Django environment
sys.path.append('/mnt/test_disque/NextSchoolAI')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nextschoolai.settings')
django.setup()

from django.conf import settings
print(f"DEBUG: {settings.DEBUG}")
print(f"GEMINI_API_KEY: '{settings.GEMINI_API_KEY}'")
