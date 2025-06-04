from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = '强制清理不再使用的权限'

    def handle(self, *args, **options):
        # 删除媒体渠道相关权限
        try:
            media_content_type = ContentType.objects.get(app_label='tasks', model='mediachannel')
            Permission.objects.filter(content_type=media_content_type).delete()
            self.stdout.write(self.style.SUCCESS('成功删除媒体渠道相关权限'))
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.SUCCESS('媒体渠道内容类型不存在，无需删除权限'))

        # 删除其他不再使用的权限
        remaining = Permission.objects.filter(codename__contains='mediachannel')
        if remaining.exists():
            remaining.delete()
            self.stdout.write(self.style.SUCCESS('成功删除其他不再使用的权限'))
        else:
            self.stdout.write(self.style.SUCCESS('没有找到其他需要删除的权限'))

        # 获取tasks应用的内容类型
        try:
            tasks_content_type = ContentType.objects.get(app_label='tasks', model='consumptionrecord')
            
            # 删除与该内容类型相关的所有权限
            permissions = Permission.objects.filter(content_type=tasks_content_type)
            count = permissions.count()
            
            if count > 0:
                self.stdout.write(self.style.WARNING(f'找到 {count} 个tasks应用的消耗记录权限，准备删除...'))
                for perm in permissions:
                    self.stdout.write(f'删除权限: {perm.content_type.app_label}.{perm.codename} (ID: {perm.id})')
                    perm.delete()
                self.stdout.write(self.style.SUCCESS('所有tasks应用的消耗记录权限已删除！'))
            else:
                self.stdout.write(self.style.SUCCESS('没有找到tasks应用的消耗记录权限，无需删除。'))
                
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.SUCCESS('tasks应用的ConsumptionRecord内容类型不存在，无需删除权限。'))
        
        # 查看剩余的消耗记录权限
        remaining = Permission.objects.filter(codename__contains='consumptionrecord')
        self.stdout.write(self.style.SUCCESS(f'剩余消耗记录权限: {remaining.count()} 个'))
        for perm in remaining:
            self.stdout.write(f'  - {perm.content_type.app_label}.{perm.codename} (ID: {perm.id})') 