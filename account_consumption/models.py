from django.db import models
from django.utils import timezone

class AccountConsumption(models.Model):
    """账户消耗记录模型"""
    # ID（自动生成ID，主键）
    id = models.AutoField(primary_key=True, verbose_name='ID')
    # 卡号（整数）
    card_number = models.CharField(max_length=50, verbose_name="卡号")
    # 有效期（字符串）
    expiry_date = models.CharField(max_length=10, verbose_name="有效期")
    # CVC（整数）
    cvc = models.CharField(max_length=10, verbose_name="CVC")
    # 完整信息（字符串）
    full_info = models.CharField(max_length=200, verbose_name="完整信息")
    # 用处/责任人（字符串）
    responsible_person = models.CharField(max_length=50, verbose_name="用处/责任人")
    # 编号（字符串）
    serial_number = models.CharField(max_length=50, verbose_name="编号")
    # BM名称（字符串）
    bm_name = models.CharField(max_length=50, verbose_name="BM名称")
    # 是否限额（字符串）
    has_limit = models.CharField(max_length=10, choices=[('是', '是'), ('否', '否')], default='否', verbose_name="是否限额")
    # 账户ID（整数）
    account_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="账户ID")
    # 账户状态（字符串）
    account_status = models.CharField(max_length=20, choices=[('正常', '正常'), ('待激活', '待激活'), ('已冻结', '已冻结'), ('已关闭', '已关闭')], default='正常', verbose_name="账户状态")
    # 卡台（字符串）
    card_platform = models.CharField(max_length=20, verbose_name="卡台")
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 更新时间
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '账户消耗'
        verbose_name_plural = '账户消耗'
        ordering = ['-created_at']  # 默认按创建时间倒序排列

    def __str__(self):
        return f"{self.card_number} - {self.responsible_person}"

class MonthlyConsumption(models.Model):
    # 使用Django默认的自动递增ID字段
    account = models.ForeignKey(AccountConsumption, on_delete=models.CASCADE, related_name='monthly_consumptions', verbose_name="关联账户")
    year = models.IntegerField(verbose_name="年份")
    month = models.IntegerField(verbose_name="月份")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="消耗金额")
    remark = models.TextField(blank=True, null=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "月度消耗"
        verbose_name_plural = "月度消耗"
        unique_together = ('account', 'year', 'month')  # 确保每个账户每月只有一条记录
        ordering = ['-year', '-month']  # 按年月倒序排列
        
    def __str__(self):
        return f"{self.account.card_number} - {self.year}年{self.month}月"
    
    @property
    def month_display(self):
        """格式化显示月份，例如：2023年05月"""
        return f"{self.year}年{self.month:02d}月"
