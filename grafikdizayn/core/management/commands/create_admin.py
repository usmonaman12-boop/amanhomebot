from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Admin rolidagi foydalanuvchi yaratadi (login panel uchun)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--first_name", default="Admin")
        parser.add_argument("--last_name", default="")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        if User.objects.filter(username=username).exists():
            raise CommandError(f"Username '{username}' allaqachon mavjud.")
        user = User.objects.create_superuser(
            username=username,
            password=options["password"],
            first_name=options["first_name"],
            last_name=options["last_name"],
        )
        user.role = User.ROLE_ADMIN
        user.save(update_fields=["role"])
        self.stdout.write(self.style.SUCCESS(f"Admin '{username}' yaratildi."))
