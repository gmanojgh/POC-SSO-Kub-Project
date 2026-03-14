from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Report, User
from .serializers import ReportSerializer, ReportCreateSerializer, UserSerializer
from .permissions import CanViewReports, CanCreateReports, CanDeleteReports, CanManageUsers
 
 
class MeView(APIView):
    def get(self, request):
        print(f"User: {request.user}, Auth: {request.auth}, ID: {request.user.id}")
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
 
 
class ReportListView(APIView):
    permission_classes = [CanViewReports]
 
    def get(self, request):
        """List all active reports"""
        reports = Report.objects.filter(is_active=True).select_related('created_by')
        serializer = ReportSerializer(reports, many=True)
        return Response({
            "count": reports.count(),
            "results": serializer.data
        }) 
 
class ReportCreateView(APIView):
    permission_classes = [CanCreateReports]
 
    def post(self, request):
        """Create a new report"""
        serializer = ReportCreateSerializer(data=request.data)
        if serializer.is_valid():
            report = serializer.save(created_by=request.user)
            return Response(
                ReportSerializer(report).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
 
class ReportDetailView(APIView):
    permission_classes = [CanViewReports]
 
    def get_object(self, pk):
        try:
            return Report.objects.get(pk=pk, is_active=True)
        except Report.DoesNotExist:
            return None
 
    def get(self, request, pk):
        report = self.get_object(pk)
        if not report:
            return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(ReportSerializer(report).data)
 
    def delete(self, request, pk):
        """Soft delete — checks delete permission separately"""
        if not request.user.has_permission('delete_reports'):
            return Response({"error": "You do not have permission to delete reports"},
                            status=status.HTTP_403_FORBIDDEN)
        report = self.get_object(pk)
        if not report:
            return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)
        report.is_active = False
        report.save()
        return Response({"message": f"Report '{report.title}' deleted"})
 
 
class UserListView(APIView):
    permission_classes = [CanManageUsers]
 
    def get(self, request):
        """Admin only — list all users with their roles"""
        users = User.objects.all().select_related('role')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
