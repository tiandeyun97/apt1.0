import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class Company(models.Model):
    STATUS_CHOICES = [
        ('normal', '正常'),
        ('suspended', '暂停'),
        ('closed', '关闭'),
    ]
    
    company_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name='公司ID')
    company_name = models.CharField(max_length=200, verbose_name='公司名称')
    company_code = models.CharField(max_length=50, unique=True, verbose_name='公司编号')
    address = models.CharField(max_length=500, verbose_name='公司地址')
    contact_person = models.CharField(max_length=100, null=True, blank=True, verbose_name='联系人')
    contact_email = models.EmailField(null=True, blank=True, verbose_name='联系邮箱')
    contact_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='联系电话')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal', verbose_name='状态')

    class Meta:
        verbose_name = '公司管理'
        verbose_name_plural = '公司管理'
        ordering = ['-create_date']

    def __str__(self):
        return self.company_name

class User(AbstractUser):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name='所属公司',
        related_name='users',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = '用户管理'
        verbose_name_plural = '用户管理'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.company.company_name if self.company else '未分配公司'})"

class Department(models.Model):
    STATUS_CHOICES = [
        ('normal', '正常'),
        ('suspended', '暂停'),
        ('closed', '关闭')
    ]

    department_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name='部门ID')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='所属公司')
    department_code = models.CharField(max_length=50, verbose_name='部门编号')
    department_name = models.CharField(max_length=100, verbose_name='部门名称')
    parent_department = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                        verbose_name='上级部门', related_name='child_departments')
    manager = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name='部门负责人', related_name='managed_department')
    members = models.ManyToManyField(User, blank=True, 
                                   verbose_name='部门成员', related_name='department')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal', verbose_name='状态')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '部门管理'
        verbose_name_plural = '部门管理'
        ordering = ['department_code']
        unique_together = [['company', 'department_code']]

    def __str__(self):
        return f"{self.company.company_name} - {self.department_name}"

    @property
    def member_count(self):
        return self.members.count()