from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission

class Command(BaseCommand):
    help = '清理不再使用的权限'

    def handle(self, *args, **options):
        # 删除不再使用的权限
        Permission.objects.filter(
            codename__contains='mediachannel'
        ).delete()

        self.stdout.write(self.style.SUCCESS('成功清理不再使用的权限')) 