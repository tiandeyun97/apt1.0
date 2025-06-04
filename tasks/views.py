from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count
from .models import Project, MediaChannel, TaskType, TaskStatus
from organize.models import Company, Department, User
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import redirect
from django.db import models
from django.utils import timezone
from .permissions import (
    MediaChannelPermissionMixin,
    TaskTypePermissionMixin,
    TaskStatusPermissionMixin,
    ProjectPermissionMixin
)
import logging
from .api import project_detail_api, get_optimizers
from django.contrib import admin
from .forms import ProjectForm, MediaChannelForm, TaskTypeForm, TaskStatusForm

logger = logging.getLogger(__name__)

# Create your views here.

# 项目视图
class ProjectListView(LoginRequiredMixin, ProjectPermissionMixin, ListView):
    """项目列表视图"""
    model = Project
    template_name = 'tasks/project_list.html'
    context_object_name = 'projects'
    action = 'view'

class ProjectCreateView(LoginRequiredMixin, ProjectPermissionMixin, CreateView):
    """项目创建视图"""
    model = Project
    form_class = ProjectForm
    template_name = 'tasks/project_form.html'
    action = 'add'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.CompanyID = self.request.user.company
        messages.success(self.request, f"项目 '{form.instance.ProjectName}' 创建成功！")
        return super().form_valid(form)

    def get_success_url(self):
        # 检查表单提交中是否有返回URL参数
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        
        # 如果没有next参数，检查请求的referer
        referer = self.request.META.get('HTTP_REFERER')
        if referer and 'admin/tasks/project' in referer and ('?p=' in referer or '&p=' in referer or 'list_per_page' in referer or 'q=' in referer):
            return referer
            
        # 如果没有有效的referer，返回默认URL
        return reverse_lazy('admin:tasks_project_changelist')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取referer并传递给模板，用于返回按钮
        referer = self.request.META.get('HTTP_REFERER')
        if referer and 'admin/tasks/project' in referer:
            context['referer_url'] = referer
        else:
            context['referer_url'] = reverse_lazy('admin:tasks_project_changelist')
        return context

class ProjectUpdateView(LoginRequiredMixin, ProjectPermissionMixin, UpdateView):
    """项目更新视图"""
    model = Project
    form_class = ProjectForm
    template_name = 'tasks/project_form.html'
    action = 'change'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"项目 '{form.instance.ProjectName}' 更新成功！")
        return super().form_valid(form)

    def get_success_url(self):
        # 检查表单提交中是否有返回URL参数
        next_url = self.request.POST.get('next')
        if next_url:
            return next_url
        
        # 如果没有next参数，检查请求的referer
        referer = self.request.META.get('HTTP_REFERER')
        if referer and 'admin/tasks/project' in referer and ('?p=' in referer or '&p=' in referer or 'list_per_page' in referer or 'q=' in referer):
            return referer
            
        # 如果没有有效的referer，返回默认URL
        return reverse_lazy('admin:tasks_project_changelist')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取referer并传递给模板，用于返回按钮
        referer = self.request.META.get('HTTP_REFERER')
        if referer and 'admin/tasks/project' in referer:
            context['referer_url'] = referer
        else:
            context['referer_url'] = reverse_lazy('admin:tasks_project_changelist')
        return context

# 媒体渠道视图
class MediaChannelListView(LoginRequiredMixin, MediaChannelPermissionMixin, ListView):
    """媒体渠道列表视图"""
    model = MediaChannel
    template_name = 'tasks/media_channel_list.html'
    context_object_name = 'media_channels'
    action = 'view'

class MediaChannelDetailView(LoginRequiredMixin, MediaChannelPermissionMixin, DetailView):
    """媒体渠道详情视图"""
    model = MediaChannel
    template_name = 'tasks/media_channel_detail.html'
    context_object_name = 'media_channel'
    action = 'view'

class MediaChannelCreateView(LoginRequiredMixin, MediaChannelPermissionMixin, CreateView):
    """媒体渠道创建视图"""
    model = MediaChannel
    template_name = 'tasks/media_channel_form.html'
    fields = ['MediaChannelName', 'Description']
    success_url = reverse_lazy('tasks:media_channel_list')
    action = 'add'

    def form_valid(self, form):
        form.instance.CompanyID = self.request.user.company
        return super().form_valid(form)

class MediaChannelUpdateView(LoginRequiredMixin, MediaChannelPermissionMixin, UpdateView):
    """媒体渠道更新视图"""
    model = MediaChannel
    template_name = 'tasks/media_channel_form.html'
    fields = ['MediaChannelName', 'Description']
    action = 'change'

    def get_success_url(self):
        return reverse('tasks:media_channel_detail', kwargs={'pk': self.object.pk})

class MediaChannelDeleteView(LoginRequiredMixin, MediaChannelPermissionMixin, DeleteView):
    """媒体渠道删除视图"""
    model = MediaChannel
    template_name = 'tasks/media_channel_confirm_delete.html'
    success_url = reverse_lazy('tasks:media_channel_list')
    action = 'delete'

# 任务类型视图
class TaskTypeListView(LoginRequiredMixin, TaskTypePermissionMixin, ListView):
    """任务类型列表视图"""
    model = TaskType
    template_name = 'tasks/task_type_list.html'
    context_object_name = 'task_types'
    action = 'view'

class TaskTypeDetailView(LoginRequiredMixin, TaskTypePermissionMixin, DetailView):
    """任务类型详情视图"""
    model = TaskType
    template_name = 'tasks/task_type_detail.html'
    context_object_name = 'task_type'
    action = 'view'

class TaskTypeCreateView(LoginRequiredMixin, TaskTypePermissionMixin, CreateView):
    """任务类型创建视图"""
    model = TaskType
    template_name = 'tasks/task_type_form.html'
    fields = ['TaskTypeName', 'Description']
    success_url = reverse_lazy('tasks:task_type_list')
    action = 'add'

    def form_valid(self, form):
        form.instance.CompanyID = self.request.user.company
        return super().form_valid(form)

class TaskTypeUpdateView(LoginRequiredMixin, TaskTypePermissionMixin, UpdateView):
    """任务类型更新视图"""
    model = TaskType
    template_name = 'tasks/task_type_form.html'
    fields = ['TaskTypeName', 'Description']
    action = 'change'

    def get_success_url(self):
        return reverse('tasks:task_type_detail', kwargs={'pk': self.object.pk})

class TaskTypeDeleteView(LoginRequiredMixin, TaskTypePermissionMixin, DeleteView):
    """任务类型删除视图"""
    model = TaskType
    template_name = 'tasks/task_type_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_type_list')
    action = 'delete'

# 任务状态视图
class TaskStatusListView(LoginRequiredMixin, TaskStatusPermissionMixin, ListView):
    """任务状态列表视图"""
    model = TaskStatus
    template_name = 'tasks/task_status_list.html'
    context_object_name = 'task_statuses'
    action = 'view'

class TaskStatusDetailView(LoginRequiredMixin, TaskStatusPermissionMixin, DetailView):
    """任务状态详情视图"""
    model = TaskStatus
    template_name = 'tasks/task_status_detail.html'
    context_object_name = 'task_status'
    action = 'view'

class TaskStatusCreateView(LoginRequiredMixin, TaskStatusPermissionMixin, CreateView):
    """任务状态创建视图"""
    model = TaskStatus
    template_name = 'tasks/task_status_form.html'
    fields = ['TaskStatusName', 'Description']
    success_url = reverse_lazy('tasks:task_status_list')
    action = 'add'

    def form_valid(self, form):
        form.instance.CompanyID = self.request.user.company
        return super().form_valid(form)

class TaskStatusUpdateView(LoginRequiredMixin, TaskStatusPermissionMixin, UpdateView):
    """任务状态更新视图"""
    model = TaskStatus
    template_name = 'tasks/task_status_form.html'
    fields = ['TaskStatusName', 'Description']
    action = 'change'

    def get_success_url(self):
        return reverse('tasks:task_status_detail', kwargs={'pk': self.object.pk})

class TaskStatusDeleteView(LoginRequiredMixin, TaskStatusPermissionMixin, DeleteView):
    """任务状态删除视图"""
    model = TaskStatus
    template_name = 'tasks/task_status_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_status_list')
    action = 'delete'


