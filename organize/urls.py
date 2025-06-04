from django.urls import path
from . import views

app_name = 'organize'

urlpatterns = [
    path('company/', views.CompanyListView.as_view(), name='company-list'),
    path('company/add/', views.CompanyCreateView.as_view(), name='company-add'),
    path('company/<uuid:pk>/edit/', views.CompanyUpdateView.as_view(), name='company-edit'),
    path('company/<uuid:pk>/delete/', views.CompanyDeleteView.as_view(), name='company-delete'),
    
    path('department/', views.DepartmentListView.as_view(), name='department-list'),
    path('department/add/', views.DepartmentCreateView.as_view(), name='department-add'),
    path('department/<str:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department-edit'),
    path('department/<str:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department-delete'),
] 