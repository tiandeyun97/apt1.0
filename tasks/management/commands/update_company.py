from django.core.management.base import BaseCommand
from tasks.models import MediaChannel, TaskType, TaskStatus, Project
from organize.models import Company

class Command(BaseCommand):
    help = '为现有的媒体渠道、任务类型、任务状态和项目更新公司字段'

    def add_arguments(self, parser):
        parser.add_argument('company_id', type=str, help='要设置的公司ID')

    def handle(self, *args, **options):
        try:
            company = Company.objects.get(pk=options['company_id'])
            
            # 更新媒体渠道
            MediaChannel.objects.filter(CompanyID__isnull=True).update(CompanyID=company)
            self.stdout.write(self.style.SUCCESS(f'成功更新媒体渠道的公司字段'))

            # 更新任务类型
            TaskType.objects.filter(CompanyID__isnull=True).update(CompanyID=company)
            self.stdout.write(self.style.SUCCESS(f'成功更新任务类型的公司字段'))

            # 更新任务状态
            TaskStatus.objects.filter(CompanyID__isnull=True).update(CompanyID=company)
            self.stdout.write(self.style.SUCCESS(f'成功更新任务状态的公司字段'))

            # 更新项目
            Project.objects.filter(CompanyID__isnull=True).update(CompanyID=company)
            self.stdout.write(self.style.SUCCESS(f'成功更新项目的公司字段'))

        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'找不到指定的公司ID: {options["company_id"]}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'更新过程中出错: {str(e)}')) 