"""
WSGI config for kernel_cases project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')

application = get_wsgi_application()