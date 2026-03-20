from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Delete all app data while keeping the megaglow admin login."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-username",
            default="megaglow",
            help="Username to preserve (default: megaglow)",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirm deletion without prompting.",
        )

    def handle(self, *args, **options):
        keep_username = options["keep_username"]
        assume_yes = options["yes"]

        if not assume_yes:
            self.stdout.write(self.style.WARNING(
                "This will permanently delete PRODUCTS, SALES, and TODOS data from the database.\n"
                f"It will keep the login user: {keep_username}\n"
                "Run again with --yes to confirm."
            ))
            return

        User = get_user_model()

        # Import models lazily so Django app registry is ready
        from products.models import Product
        from sales.models import Sale
        from todos.models import RestockTodo

        deleted = {}

        with transaction.atomic():
            # Delete app data (order matters for FK constraints)
            deleted["sales"] = Sale.objects.all().delete()[0]
            deleted["restock_todos"] = RestockTodo.objects.all().delete()[0]
            deleted["products"] = Product.objects.all().delete()[0]

            # Keep only the specified admin user
            keep_user = User.objects.filter(username=keep_username).first()
            if keep_user:
                deleted["other_users"] = User.objects.exclude(pk=keep_user.pk).delete()[0]
            else:
                deleted["other_users"] = 0

            # Keep token for the preserved admin user, delete other tokens
            try:
                from rest_framework.authtoken.models import Token
                if keep_user:
                    deleted["other_tokens"] = Token.objects.exclude(user=keep_user).delete()[0]
                else:
                    deleted["other_tokens"] = Token.objects.all().delete()[0]
            except Exception:
                deleted["other_tokens"] = 0

        self.stdout.write(self.style.SUCCESS("Database cleared (admin login preserved)."))
        for k, v in deleted.items():
            self.stdout.write(f"- {k}: {v} deleted")

