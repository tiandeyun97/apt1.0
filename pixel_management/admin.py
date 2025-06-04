from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .models import Pixel

# 注册权限模型
admin.site.register(Permission)

@admin.register(Pixel)
class PixelAdmin(admin.ModelAdmin):
    list_display = ('pixel_id', 'task', 'bm_id', 'account', 'timezone', 'is_authorized', 'creator', 'created_at', 'updated_at')
    list_filter = ('is_authorized', 'created_at', 'creator')
    search_fields = ('pixel_id', 'task__name', 'bm_id', 'account')
    readonly_fields = ('creator', 'created_at', 'updated_at')
    autocomplete_fields = ['task']
    
    def save_model(self, request, obj, form, change):
        if not change:  # 只在创建时设置创建者
            obj.creator = request.user
        super().save_model(request, obj, form, change)
    
    # 自定义URLs
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_site.admin_view(self.pixel_list_view), name='pixel_management_pixel_changelist'),
            path('add/', self.admin_site.admin_view(self.pixel_create_view), name='pixel_management_pixel_add'),
            path('<int:pk>/change/', self.admin_site.admin_view(self.pixel_edit_view), name='pixel_management_pixel_change'),
            # Admin详情页通常不覆盖，但如果需要，可以添加类似的URL模式
            # path('<int:pk>/debug/', self.admin_site.admin_view(self.pixel_detail_view), name='pixel_management_pixel_detail'),
        ]
        return custom_urls + urls
    
    # 自定义视图
    @method_decorator(staff_member_required)
    def pixel_list_view(self, request):
        from .views import pixel_list
        return pixel_list(request)
    
    @method_decorator(staff_member_required)
    def pixel_create_view(self, request):
        from .views import pixel_create
        return pixel_create(request)
    
    @method_decorator(staff_member_required)
    def pixel_edit_view(self, request, pk):
        from .views import pixel_edit
        return pixel_edit(request, pk)
    
    # 我们在列表页的操作按钮中直接链接到详情页视图，因此Admin中不需要详情页的自定义URL
    # @method_decorator(staff_member_required)
    # def pixel_detail_view(self, request, pk):
    #     from .views import pixel_detail
    #     return pixel_detail(request, pk)
    
    # 启用自动完成和跨域资源
    class Media:
        js = (
            'admin/js/jquery.init.js', 
            'admin/js/autocomplete.js',
            # CDN资源引用，解决跨域问题
            'https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.1.3/js/bootstrap.bundle.min.js',
            'https://cdn.bootcdn.net/ajax/libs/jquery/3.6.0/jquery.min.js',
            'https://cdn.bootcdn.net/ajax/libs/select2/4.1.0-rc.0/js/select2.min.js',
        )
        css = {
            'all': (
                'https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.1.3/css/bootstrap.min.css',
                'https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/css/all.min.css',
                'https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap',
                'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
                'https://cdn.jsdelivr.net/npm/select2-bootstrap-5-theme@1.3.0/dist/select2-bootstrap-5-theme.min.css',
            )
        }
    
    fieldsets = (
        ('基本信息', {
            'fields': ('pixel_id', 'task', 'bm_id')
        }),
        ('账户信息', {
            'fields': ('account', 'timezone')
        }),
        ('授权信息', {
            'fields': ('is_authorized', 'notes')
        }),
        ('创建信息', {
            'fields': ('creator', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
