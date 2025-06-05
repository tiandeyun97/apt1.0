# 开发环境配置指南

## 环境需求

在开始广告投放管理平台的开发工作前，请确保您的系统满足以下基本需求：

### 基础软件

- **Python 3.8+** - 运行Django框架的基础
- **PostgreSQL 12+** - 数据库系统
- **Git** - 版本控制
- **pip** - Python包管理工具
- **virtualenv** 或 **venv** - Python虚拟环境
- **Node.js 14+** (可选) - 用于前端资源构建

## 开发环境搭建步骤

### 1. 克隆代码库

```bash
git clone https://github.com/your-organization/ad-management-platform.git
cd ad-management-platform
```

### 2. 创建并激活虚拟环境

#### Windows环境

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux/MacOS环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装项目依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 安装开发环境特定的依赖
```

### 4. 配置本地设置

从模板创建本地设置文件：

```bash
cp ad_manplat/settings_local_template.py ad_manplat/settings_local.py
```

编辑 `settings_local.py` 文件，更新以下关键配置：

```python
# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_local_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# 开发环境设置
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# 邮件设置（可选）
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### 5. 准备数据库

#### 创建PostgreSQL数据库

```bash
# 登录PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE ad_management_dev;

# 创建用户（如需要）
CREATE USER ad_dev WITH PASSWORD 'your_password';

# 授予权限
GRANT ALL PRIVILEGES ON DATABASE ad_management_dev TO ad_dev;

# 退出PostgreSQL
\q
```

#### 执行数据库迁移

```bash
python manage.py migrate
```

### 6. 创建超级用户

```bash
python manage.py createsuperuser
```

### 7. 收集静态文件

```bash
python manage.py collectstatic
```

### 8. 启动开发服务器

```bash
python manage.py runserver
```

现在，您可以通过浏览器访问 http://127.0.0.1:8000/ 来查看应用。

## 开发工具推荐

### 集成开发环境/编辑器

- **Visual Studio Code** - 带有Python和Django扩展
- **PyCharm Professional** - 提供完整的Django支持
- **Sublime Text** - 轻量级选择

### VS Code 推荐扩展

- **Python** - Python语言支持
- **Pylance** - Python静态类型检查
- **Django** - Django语法高亮和支持
- **PostgreSQL** - 数据库查询和管理
- **GitLens** - Git增强功能
- **Prettier** - 代码格式化

### PyCharm 配置

1. 打开项目
2. 配置项目解释器，指向您的虚拟环境
3. 在设置中启用Django支持
4. 配置Django项目根目录和settings文件

## 开发规范与流程

### 代码风格

项目遵循PEP 8的Python代码风格规范，并使用以下工具进行代码质量控制：

- **flake8** - 代码风格检查
- **black** - 代码格式化
- **isort** - 导入语句排序

运行代码风格检查：

```bash
# 检查代码风格
flake8 .

# 自动格式化代码
black .

# 排序导入语句
isort .
```

### Git工作流

1. 从主分支创建功能分支：`git checkout -b feature/your-feature`
2. 完成功能开发并添加测试
3. 运行代码风格检查和测试
4. 提交代码：`git commit -am "详细描述您的变更"`
5. 推送到远程：`git push origin feature/your-feature`
6. 创建Pull Request请求合并到主分支

### 测试

运行测试：

```bash
# 运行所有测试
python manage.py test

# 运行特定应用的测试
python manage.py test app_name

# 运行单个测试类
python manage.py test app_name.tests.TestClassName

# 生成测试覆盖率报告
coverage run --source='.' manage.py test
coverage report
```

## 调试技巧

### Django Debug Toolbar

Django Debug Toolbar已配置在开发环境中。当DEBUG=True时，您将在浏览器右侧看到调试工具栏，它提供：

- SQL查询分析
- 请求/响应信息
- 缓存操作
- 信号追踪
- 模板渲染信息

### 日志配置

项目配置了不同级别的日志记录。您可以在开发时使用：

```python
import logging
logger = logging.getLogger(__name__)

# 在代码中使用
logger.debug('调试信息')
logger.info('信息')
logger.warning('警告')
logger.error('错误')
```

## 常见问题解决

### 数据库连接问题

1. 检查PostgreSQL服务是否正在运行
2. 验证数据库凭据是否正确
3. 确认防火墙/网络设置允许连接

### 静态文件不加载

1. 确保已运行`collectstatic`命令
2. 检查`STATIC_URL`和`STATIC_ROOT`设置
3. 在开发环境中，确保`DEBUG=True`

### 模块导入错误

1. 确认虚拟环境已激活
2. 检查是否安装了所有依赖项
3. 尝试重新安装问题依赖：`pip install -U package_name`

### 迁移冲突

1. 检查并删除冲突的迁移文件
2. 重新生成迁移：`python manage.py makemigrations`
3. 如有需要，可使用`--fake`参数应用迁移

## 开发环境刷新

如果您需要完全重置开发环境：

```bash
# 停止服务器
# 删除数据库
dropdb ad_management_dev -U postgres

# 创建新数据库
createdb ad_management_dev -U postgres

# 删除所有迁移文件（谨慎操作）
find . -path '*/migrations/*.py' -not -path '*/migrations/__init__.py' -delete

# 重新创建迁移
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

## 本地化测试

如果您需要测试不同语言环境：

```bash
# 生成翻译文件
python manage.py makemessages -l zh_CN

# 编译翻译文件
python manage.py compilemessages
``` 