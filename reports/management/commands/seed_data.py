"""
Management command to seed the database with initial roles, permissions,
and test users.

Safe to run multiple times — uses get_or_create throughout.

Usage:
    python manage.py seed_data
    python manage.py seed_data --reset   # wipes and re-seeds test users
"""

import logging

from django.core.management.base import BaseCommand, CommandError

from reports.models import Permission, Role, RolePermission, User

logger = logging.getLogger(__name__)

# ─── Permission definitions ───────────────────────────────────────────────────

PERMISSIONS = {
    "view_reports": "Can view existing reports",
    "create_reports": "Can create new reports",
    "delete_reports": "Can soft-delete reports",
    "manage_users": "Can view and manage user accounts",
}

# ─── Role → Permission mapping ────────────────────────────────────────────────

ROLE_PERMISSIONS = {
    "Admin": list(PERMISSIONS.keys()),                          # Everything
    "Manager": ["view_reports", "create_reports"],              # Read + write
    "Viewer": ["view_reports"],                                 # Read only
}

# ─── Test users ───────────────────────────────────────────────────────────────

TEST_USERS = [
    {"username": "alice", "email": "alice@example.com", "password": "password123", "role": "Admin"},
    {"username": "bob",   "email": "bob@example.com",   "password": "password123", "role": "Manager"},
    {"username": "carol", "email": "carol@example.com", "password": "password123", "role": "Viewer"},
]


class Command(BaseCommand):
    help = "Seed roles, permissions, and test users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing test users before re-seeding (roles/permissions are always safe)",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            usernames = [u["username"] for u in TEST_USERS]
            deleted, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing test users"))

        # ── 1. Permissions ────────────────────────────────────────────────
        perm_objects = {}
        for name, description in PERMISSIONS.items():
            perm, created = Permission.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            perm_objects[name] = perm
            if created:
                self.stdout.write(f"  Created permission: {name}")

        # ── 2. Roles ──────────────────────────────────────────────────────
        role_objects = {}
        for role_name in ROLE_PERMISSIONS:
            role, created = Role.objects.get_or_create(name=role_name)
            role_objects[role_name] = role
            if created:
                self.stdout.write(f"  Created role: {role_name}")

        # ── 3. Role → Permission assignments ─────────────────────────────
        for role_name, perm_names in ROLE_PERMISSIONS.items():
            role = role_objects[role_name]
            for perm_name in perm_names:
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=perm_objects[perm_name],
                )

        # ── 4. Test users ─────────────────────────────────────────────────
        created_count = 0
        for user_data in TEST_USERS:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={"email": user_data["email"]},
            )
            if created:
                user.set_password(user_data["password"])
                user.role = role_objects[user_data["role"]]
                user.save()
                created_count += 1
                self.stdout.write(
                    f"  Created user: {user.username} ({user_data['role']})"
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"  Skipped existing user: {user.username}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeed complete: "
                f"{len(PERMISSIONS)} permissions, "
                f"{len(ROLE_PERMISSIONS)} roles, "
                f"{created_count} users created"
            )
        )
