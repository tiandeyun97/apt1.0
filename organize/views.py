from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Company, Department, User
from .permissions import CompanyPermissionMixin, DepartmentPermissionMixin, UserPermissionMixin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.forms import ModelChoiceField
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

# Admin视图类
class AdminUserAdmin(BaseUserAdmin):
    """用户后台管理视图"""
    list_display = ('username', 'email', 'company', 'get_department', 'is_staff', 'is_active', 'get_groups')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'company', 'groups', 'department')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'department__department_name')
    ordering = ('username',)
    filter_horizontal = ('groups',)

    def get_groups(self, obj):
        return ', '.join([group.name for group in obj.groups.all()])
    get_groups.short_description = '用户组'

    def get_department(self, obj):
        if hasattr(obj, 'department') and obj.department.first():
            return obj.department.first().department_name
        return '-'
    get_department.short_description = '所属部门'

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'company', 'is_staff', 'is_active', 'groups'),
        }),
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email')}),
        ('权限信息', {
            'fields': ('company', 'is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )

    def response_add(self, request, obj, post_url_continue=None):
        """重写用户添加后的响应方法"""
        return self.response_post_save_add(request, obj)

    def response_post_save_add(self, request, obj):
        """自定义保存后的响应"""
        return HttpResponseRedirect(reverse('admin:organize_user_changelist'))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)

    def has_module_permission(self, request):
        """检查用户是否有访问用户管理模块的权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('organize.view_user')

    def has_view_permission(self, request, obj=None):
        """检查用户是否有查看权限"""
        if request.user.is_superuser:
            return True
        if not request.user.has_perm('organize.view_user'):
            return False
        if obj and request.user.company != obj.company:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        """检查用户是否有修改权限"""
        if request.user.is_superuser:
            return True
        if not request.user.has_perm('organize.change_user'):
            return False
        if obj and request.user.company != obj.company:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        """检查用户是否有删除权限"""
        if not super().has_delete_permission(request, obj):
            return False
        return True

    def has_add_permission(self, request):
        """检查用户是否有添加权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('organize.add_user')

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return self.readonly_fields + ('company',)
        return self.readonly_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "company":
            if request.user.is_superuser:
                # 超级管理员可以选择所有公司
                kwargs["queryset"] = Company.objects.all()
            else:
                # 普通用户只能选择其所属公司
                kwargs["queryset"] = Company.objects.filter(pk=request.user.company.pk)
                kwargs["initial"] = request.user.company
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class AdminCompanyAdmin(admin.ModelAdmin):
    """公司后台管理视图"""
    list_display = ('company_name', 'company_code', 'status', 'get_departments_count', 'get_users_count')
    search_fields = ('company_name', 'company_code')
    list_filter = ('status',)

    def get_departments_count(self, obj):
        return obj.department_set.count()
    get_departments_count.short_description = '部门数量'

    def get_users_count(self, obj):
        return obj.users.count()
    get_users_count.short_description = '用户数量'

    def has_module_permission(self, request):
        """检查用户是否有访问公司管理模块的权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('organize.view_company')

    def has_view_permission(self, request, obj=None):
        """检查用户是否有查看权限"""
        if request.user.is_superuser:
            return True
        if not request.user.has_perm('organize.view_company'):
            return False
        if obj and request.user.company != obj:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        """检查用户是否有修改权限"""
        if request.user.is_superuser:
            return True
        if not request.user.has_perm('organize.change_company'):
            return False
        if obj and request.user.company != obj:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        """检查用户是否有删除权限"""
        if request.user.is_superuser:
            return True
        if not request.user.has_perm('organize.delete_company'):
            return False
        if obj and request.user.company != obj:
            return False
        return True

    def has_add_permission(self, request):
        """检查用户是否有添加权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('organize.add_company')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(pk=request.user.company.pk)

class AdminDepartmentAdmin(admin.ModelAdmin):
    """部门后台管理视图"""
    list_display = ('department_name', 'department_code', 'company', 'parent_department', 'manager', 'get_members_count', 'get_child_departments_count', 'status', 'create_date')
    list_filter = ('status', 'company')
    search_fields = ('department_name', 'department_code')
    filter_horizontal = ('members',)

    def get_members_count(self, obj):
        return obj.members.count()
    get_members_count.short_description = '成员数量'

    def get_child_departments_count(self, obj):
        return obj.child_departments.count()
    get_child_departments_count.short_description = '子部门数量'

    def has_module_permission(self, request):
        """检查用户是否有访问部门管理模块的权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('organize.view_department')

    def has_view_permission(self, request, obj=None):
        """检查用户是否有查看权限"""
        if request.user.is_superuser:
            return True
        if not request.user.has_perm('organize.view_department'):
            return False
        if obj and request.user.company != obj.company:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        """检查用户是否有修改权限"""
        if request.user.is_superuser:
            return True
        if not request.user.has_perm('organize.change_department'):
            return False
        if obj and request.user.company != obj.company:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        """检查用户是否有删除权限"""
        if request.user.is_superuser:
            return True
        if not request.user.has_perm('organize.delete_department'):
            return False
        if obj and request.user.company != obj.company:
            return False
        return True

    def has_add_permission(self, request):
        """检查用户是否有添加权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('organize.add_department')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "company":
                kwargs["queryset"] = Company.objects.filter(pk=request.user.company.pk)
                kwargs["initial"] = request.user.company
            elif db_field.name == "parent_department":
                class DepartmentChoiceField(ModelChoiceField):
                    def label_from_instance(self, obj):
                        return f"{obj.department_name} ({obj.department_code}) - {obj.get_status_display()}"
                
                kwargs["form_class"] = DepartmentChoiceField
                kwargs["queryset"] = Department.objects.filter(company=request.user.company).order_by('department_code')
            elif db_field.name == "manager":
                # 获取当前正在编辑的部门对象
                obj = self.get_object(request, request.resolver_match.kwargs.get('object_id'))
                
                # 只显示部门主管和小组长角色的用户
                base_query = User.objects.filter(
                    company=request.user.company,
                    groups__name__in=['部门主管', '小组长'],
                    is_active=True
                )
                
                # 创建查询条件：未分配为其他部门的负责人，或者是当前部门的负责人
                if obj and obj.manager:
                    # 编辑现有部门时，包括当前部门的负责人和未分配的用户
                    kwargs["queryset"] = base_query.filter(
                        Q(managed_department__isnull=True) |  # 未被分配为其他部门的负责人
                        Q(id=obj.manager.id)  # 当前部门的负责人
                    ).distinct()
                else:
                    # 新建部门时，只显示未分配的用户
                    kwargs["queryset"] = base_query.filter(
                        managed_department__isnull=True  # 未被分配为其他部门的负责人
                    ).distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """处理多对多字段的表单字段"""
        if not request.user.is_superuser:
            if db_field.name == "members":
                # 获取当前正在编辑的部门对象
                obj = self.get_object(request, request.resolver_match.kwargs.get('object_id'))
                
                # 基础查询：同公司的优化师
                base_query = User.objects.filter(
                    company=request.user.company,
                    groups__name='优化师',
                    is_active=True
                )
                
                # 排除已经在其他部门的用户
                if obj:
                    # 如果是编辑现有部门，排除其他部门的成员（但保留当前部门的成员）
                    kwargs["queryset"] = base_query.filter(
                        Q(department__isnull=True) |  # 未分配部门的用户
                        Q(department=obj)  # 当前部门的用户
                    ).distinct()
                else:
                    # 如果是新建部门，只显示未分配部门的用户
                    kwargs["queryset"] = base_query.filter(
                        department__isnull=True  # 只显示未分配部门的用户
                    ).distinct()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(company=request.user.company)

# 前台视图类
class CompanyListView(LoginRequiredMixin, CompanyPermissionMixin, ListView):
    """公司列表视图
    
    显示所有公司的列表。
    
    权限要求:
        - 用户必须登录
        - 用户必须有 organize.view_company 权限（组织架构|公司|查看）
    """
    model = Company
    template_name = 'organize/company_list.html'
    context_object_name = 'companies'
    action = 'view'

class CompanyDetailView(LoginRequiredMixin, CompanyPermissionMixin, DetailView):
    """公司详情视图"""
    model = Company
    template_name = 'organize/company_detail.html'
    context_object_name = 'company'
    action = 'view'

class CompanyCreateView(LoginRequiredMixin, CompanyPermissionMixin, CreateView):
    """公司创建视图
    
    创建新的公司。
    
    权限要求:
        - 用户必须登录
        - 用户必须有 organize.add_company 权限（组织架构|公司|添加）
    """
    model = Company
    template_name = 'organize/company_form.html'
    fields = ['company_name', 'company_code', 'address', 'contact_person', 
              'contact_email', 'contact_phone', 'status']
    success_url = reverse_lazy('company-list')
    action = 'add'

class CompanyUpdateView(LoginRequiredMixin, CompanyPermissionMixin, UpdateView):
    """公司更新视图
    
    更新现有公司的信息。
    
    权限要求:
        - 用户必须登录
        - 用户必须有 organize.change_company 权限（组织架构|公司|修改）
    """
    model = Company
    template_name = 'organize/company_form.html'
    fields = ['company_name', 'company_code', 'address', 'contact_person', 
              'contact_email', 'contact_phone', 'status']
    success_url = reverse_lazy('company-list')
    action = 'change'

class CompanyDeleteView(LoginRequiredMixin, CompanyPermissionMixin, DeleteView):
    """公司删除视图
    
    删除现有公司。
    
    权限要求:
        - 用户必须登录
        - 用户必须有 organize.delete_company 权限（组织架构|公司|删除）
    """
    model = Company
    template_name = 'organize/company_confirm_delete.html'
    success_url = reverse_lazy('company-list')
    action = 'delete'

# 部门管理视图
class DepartmentListView(LoginRequiredMixin, DepartmentPermissionMixin, ListView):
    """部门列表视图
    
    显示所有部门的列表。
    
    权限要求:
        - 用户必须登录
        - 用户必须有 organize.view_department 权限（组织架构|部门|查看）
    """
    model = Department
    template_name = 'organize/department_list.html'
    context_object_name = 'departments'
    action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.filter(pk=self.request.user.company.pk)
        return context

class DepartmentDetailView(LoginRequiredMixin, DepartmentPermissionMixin, DetailView):
    """部门详情视图"""
    model = Department
    template_name = 'organize/department_detail.html'
    context_object_name = 'department'
    action = 'view'

class DepartmentCreateView(LoginRequiredMixin, DepartmentPermissionMixin, CreateView):
    """部门创建视图
    
    创建新的部门。
    
    权限要求:
        - 用户必须登录
        - 用户必须有 organize.add_department 权限（组织架构|部门|添加）
    """
    model = Department
    template_name = 'organize/department_form.html'
    fields = ['department_code', 'department_name', 'parent_department', 'manager', 'members', 'status']
    success_url = reverse_lazy('organize:department-list')
    action = 'add'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '添加部门'
        if not self.request.user.is_superuser:
            company = self.request.user.company
            context['departments'] = Department.objects.filter(company=company)
            context['users'] = User.objects.filter(company=company)
        else:
            context['departments'] = Department.objects.all()
            context['users'] = User.objects.all()
        return context

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        return super().form_valid(form)

class DepartmentUpdateView(LoginRequiredMixin, DepartmentPermissionMixin, UpdateView):
    """部门更新视图
    
    更新现有部门的信息。
    
    权限要求:
        - 用户必须登录
        - 用户必须有 organize.change_department 权限（组织架构|部门|修改）
    """
    model = Department
    template_name = 'organize/department_form.html'
    fields = ['department_code', 'department_name', 'parent_department', 'manager', 'members', 'status']
    success_url = reverse_lazy('organize:department-list')
    action = 'change'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '编辑部门'
        if not self.request.user.is_superuser:
            company = self.request.user.company
            context['departments'] = Department.objects.filter(company=company).exclude(pk=self.object.pk)
            context['users'] = User.objects.filter(company=company)
        else:
            context['departments'] = Department.objects.all().exclude(pk=self.object.pk)
            context['users'] = User.objects.all()
        return context

class DepartmentDeleteView(LoginRequiredMixin, DepartmentPermissionMixin, DeleteView):
    """部门删除视图
    
    删除现有部门。
    
    权限要求:
        - 用户必须登录
        - 用户必须有 organize.delete_department 权限（组织架构|部门|删除）
    """
    model = Department
    template_name = 'organize/department_confirm_delete.html'
    success_url = reverse_lazy('organize:department-list')
    action = 'delete'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['child_departments'] = self.object.child_departments.all()
        return context

class UserListView(LoginRequiredMixin, UserPermissionMixin, ListView):
    """用户列表视图"""
    model = User
    template_name = 'organize/user_list.html'
    context_object_name = 'users'
    action = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.filter(pk=self.request.user.company.pk)
        context['departments'] = Department.objects.filter(company=self.request.user.company)
        return context

class UserDetailView(LoginRequiredMixin, UserPermissionMixin, DetailView):
    """用户详情视图"""
    model = User
    template_name = 'organize/user_detail.html'
    context_object_name = 'user_detail'
    action = 'view'
