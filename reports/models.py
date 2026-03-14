# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
 
 
class Role(models.Model):
    """A role like Admin, Manager, Viewer"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    def __str__(self):
        return self.name
 
 
class Permission(models.Model):
    """A granular action like view_reports, delete_reports"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
 
    def __str__(self):
        return self.name
 
 
class RolePermission(models.Model):
    """Many-to-many: which permissions each role has"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
 
    class Meta:
        unique_together = ('role', 'permission')
 
 
class User(AbstractUser):
    """Extended user with a single role"""
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
 
    def has_permission(self, permission_name):
        """Check if this user's role includes the named permission"""
        if not self.role:
            return False
        return self.role.role_permissions.filter(
            permission__name=permission_name
        ).exists()
 
 
class Report(models.Model):
    """The actual resource being protected"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
 
    def __str__(self):
        return self.title
