from django.core.management.base import BaseCommand
from reports.models import Role, Permission, RolePermission, User
 
 
class Command(BaseCommand):
    help = 'Seed roles, permissions, and test users'
 
    def handle(self, *args, **kwargs):
        # Create permissions
        perms = {}
        for name in ['view_reports', 'create_reports', 'delete_reports', 'manage_users']:
            perm, _ = Permission.objects.get_or_create(name=name)
            perms[name] = perm
 
        # Create roles with their permissions
        admin_role, _ = Role.objects.get_or_create(name='Admin')
        manager_role, _ = Role.objects.get_or_create(name='Manager')
        viewer_role, _ = Role.objects.get_or_create(name='Viewer')
 
        # Admin gets everything
        for perm in perms.values():
            RolePermission.objects.get_or_create(role=admin_role, permission=perm)
 
        # Manager can view and create
        for pname in ['view_reports', 'create_reports']:
            RolePermission.objects.get_or_create(role=manager_role, permission=perms[pname])
 
        # Viewer can only view
        RolePermission.objects.get_or_create(role=viewer_role, permission=perms['view_reports'])
 
        # Create test users
        users = [
            ('alice', 'alice@example.com', 'password123', admin_role),
            ('bob', 'bob@example.com', 'password123', manager_role),
            ('carol', 'carol@example.com', 'password123', viewer_role),
        ]
        for username, email, password, role in users:
            user, created = User.objects.get_or_create(username=username, email=email)
            if created:
                user.set_password(password)
                user.role = role
                user.save()
 
        self.stdout.write(self.style.SUCCESS('Seeded: 3 roles, 4 permissions, 3 users'))
