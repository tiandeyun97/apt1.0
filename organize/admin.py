from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Company, Department
from .views import AdminUserAdmin, AdminCompanyAdmin, AdminDepartmentAdmin

# 注册模型
admin.site.register(User, AdminUserAdmin)
admin.site.register(Company, AdminCompanyAdmin)
admin.site.register(Department, AdminDepartmentAdmin)
