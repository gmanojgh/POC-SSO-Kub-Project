from django.urls import path
from reports.google_auth import GoogleSignInView   
# from .views import ...
from . import views
urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('me/', views.MeView.as_view(), name='me'),
    path('reports/', views.ReportListView.as_view(), name='report-list'),
    path('reports/create/', views.ReportCreateView.as_view(), name='report-create'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report-detail'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('api/auth/google/', GoogleSignInView.as_view(), name='google_signin'),
]