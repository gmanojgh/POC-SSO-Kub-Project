from rest_framework.permissions import BasePermission
 
 
class HasPermission(BasePermission):
    """
    Generic RBAC permission checker.
    Usage: set required_permission on your view class.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
 
        required = getattr(view, 'required_permission', None)
        if not required:
            return True  # No specific permission required
 
        return request.user.has_permission(required)
 
 
class CanViewReports(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_permission('view_reports')
 
 
class CanCreateReports(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_permission('create_reports')
 
 
class CanDeleteReports(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_permission('delete_reports')
 
 
class CanManageUsers(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_permission('manage_users')
