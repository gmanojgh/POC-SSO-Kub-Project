from rest_framework import serializers
from .models import Report, User, Role
 
 
class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
 
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions']
 
    def get_permissions(self, obj):
        return list(obj.role_permissions.values_list('permission__name', flat=True))
 
 
class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role_name', 'permissions']

    def get_role_name(self, obj):
        if not hasattr(obj, 'role') or not obj.role:
            return None
        return obj.role.name

    def get_permissions(self, obj):
        if not hasattr(obj, 'role') or not obj.role:
            return []
        return list(obj.role.role_permissions.values_list('permission__name', flat=True))
 
 
class ReportSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
 
    class Meta:
        model = Report
        fields = ['id', 'title', 'content', 'category', 'created_by_username',
                  'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_by_username', 'created_at', 'updated_at']
 
 
class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['title', 'content', 'category']
