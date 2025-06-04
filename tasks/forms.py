from django import forms
from .models import Project, MediaChannel, TaskType, TaskStatus
from organize.models import User
from django.db.models import Q

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'ProjectName', 'Description', 'StartDate', 'EndDate',
            'TimeZone', 'KPI', 'DailyReportURL', 'ManagerID',
            'TaskTypeID', 'MediaChannelID', 'Status2', 'ProductBackend'
        ]
        widgets = {
            'StartDate': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'placeholder': 'YYYY-MM-DD'
                },
                format='%Y-%m-%d'
            ),
            'EndDate': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'placeholder': 'YYYY-MM-DD'
                },
                format='%Y-%m-%d'
            ),
            'Description': forms.Textarea(attrs={'rows': 3}),
            'KPI': forms.Textarea(attrs={'rows': 1, 'style': 'height: 60px;'}),
            'Status2': forms.Select(attrs={'class': 'form-select'}),
            'TimeZone': forms.TextInput(attrs={'class': 'form-control'}),
            'ProductBackend': forms.Textarea(attrs={'rows': 3, 'style': 'height: 120px;'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # 提取并移除request参数
        super().__init__(*args, **kwargs)
        # 设置一些字段为非必填
        self.fields['Description'].required = False
        self.fields['EndDate'].required = False
        self.fields['TimeZone'].required = False
        self.fields['KPI'].required = False
        self.fields['DailyReportURL'].required = False
        self.fields['TaskTypeID'].required = False
        self.fields['MediaChannelID'].required = False
        self.fields['Status2'].required = False
        self.fields['ProductBackend'].required = False
        
        # 限制项目负责人只显示角色为"运营"的用户
        if 'ManagerID' in self.fields and self.request and hasattr(self.request.user, 'company'):
            company = self.request.user.company
            # 只显示当前公司中角色为"运营"的用户
            self.fields['ManagerID'].queryset = User.objects.filter(
                company=company,
                groups__name='运营'
            ).distinct()
            
            # 只显示当前公司的任务状态
            if 'Status2' in self.fields:
                self.fields['Status2'].queryset = TaskStatus.objects.filter(
                    CompanyID=company
                )
        
        # 如果是编辑模式，格式化已有的日期数据
        if self.instance and self.instance.pk:
            if self.instance.StartDate:
                self.initial['StartDate'] = self.instance.StartDate.strftime('%Y-%m-%d')
            if self.instance.EndDate:
                self.initial['EndDate'] = self.instance.EndDate.strftime('%Y-%m-%d')

class MediaChannelForm(forms.ModelForm):
    class Meta:
        model = MediaChannel
        fields = ['MediaChannelName', 'Description']
        
    def __init__(self, *args, **kwargs):
        self.request = getattr(self, 'request', None)
        super().__init__(*args, **kwargs)
        # 设置一些字段为非必填
        self.fields['Description'].required = False
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        # 如果是新实例且有请求对象，设置公司ID
        if not instance.pk and hasattr(self, 'request') and self.request and hasattr(self.request.user, 'company'):
            instance.CompanyID = self.request.user.company
        if commit:
            instance.save()
        return instance

class TaskTypeForm(forms.ModelForm):
    class Meta:
        model = TaskType
        fields = ['TaskTypeName', 'Description']
        
    def __init__(self, *args, **kwargs):
        self.request = getattr(self, 'request', None)
        super().__init__(*args, **kwargs)
        # 设置一些字段为非必填
        self.fields['Description'].required = False
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        # 如果是新实例且有请求对象，设置公司ID
        if not instance.pk and hasattr(self, 'request') and self.request and hasattr(self.request.user, 'company'):
            instance.CompanyID = self.request.user.company
        if commit:
            instance.save()
        return instance

class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = TaskStatus
        fields = ['TaskStatusName', 'Description']
        
    def __init__(self, *args, **kwargs):
        self.request = getattr(self, 'request', None)
        super().__init__(*args, **kwargs)
        # 设置一些字段为非必填
        self.fields['Description'].required = False
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        # 如果是新实例且有请求对象，设置公司ID
        if not instance.pk and hasattr(self, 'request') and self.request and hasattr(self.request.user, 'company'):
            instance.CompanyID = self.request.user.company
        if commit:
            instance.save()
        return instance 