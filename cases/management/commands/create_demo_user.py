"""
Management command to create demo user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a demo user for testing'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', type=str, help='Username')
        parser.add_argument('--password', default='admin123', type=str, help='Password')
        parser.add_argument('--email', default='admin@example.com', type=str, help='Email')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists')
            )
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created user "{username}" with password "{password}"')
        )