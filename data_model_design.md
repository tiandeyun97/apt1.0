# 数据库设计文档

## 概述

广告投放管理平台采用PostgreSQL数据库，实现了高效、可靠的数据存储与查询。系统的核心实体包括组织架构、项目、任务、消耗记录等，它们之间的关系构成了整个数据模型的骨架。

## 数据模型关系图

```
+---------------+     +---------------+     +---------------+
|    Company    |<-+  |  Department   |<-+  |     User      |
+---------------+  |  +---------------+  |  +---------------+
       ^           |        ^            |
       |           +--------|------------+
       |                    |
       |           +---------------+
       +---------->|    Project    |<---------+
                   +---------------+          |
                          ^                   |
                          |                   |
                   +---------------+    +---------------+
                   |   TaskType    |    |  MediaChannel |
                   +---------------+    +---------------+
                          ^
                          |
                   +---------------+    +---------------+
                   |  TaskStatus   |<---|     Task      |
                   +---------------+    +---------------+
                                                ^
                                                |
                                        +---------------+
                                        | Consumption   |
                                        +---------------+
```

## 核心数据表设计

### 组织架构相关表

#### Company (公司)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| company_id | UUID | 主键 |
| company_name | VARCHAR(200) | 公司名称 |
| company_code | VARCHAR(50) | 公司编号，唯一 |
| address | VARCHAR(500) | 公司地址 |
| contact_person | VARCHAR(100) | 联系人 |
| contact_email | VARCHAR(254) | 联系邮箱 |
| contact_phone | VARCHAR(20) | 联系电话 |
| create_date | TIMESTAMP | 创建时间 |
| status | VARCHAR(20) | 状态 |

#### Department (部门)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| department_id | UUID | 主键 |
| company_id | UUID | 外键，关联公司 |
| department_code | VARCHAR(50) | 部门编号 |
| department_name | VARCHAR(100) | 部门名称 |
| parent_department_id | UUID | 外键，关联上级部门 |
| manager_id | UUID | 外键，关联负责人 |
| status | VARCHAR(20) | 状态 |
| create_date | TIMESTAMP | 创建时间 |

#### User (用户)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| password | VARCHAR(128) | 密码哈希 |
| last_login | TIMESTAMP | 最后登录时间 |
| is_superuser | BOOLEAN | 是否为超级用户 |
| username | VARCHAR(150) | 用户名，唯一 |
| first_name | VARCHAR(150) | 名 |
| last_name | VARCHAR(150) | 姓 |
| email | VARCHAR(254) | 电子邮箱 |
| is_staff | BOOLEAN | 是否为员工 |
| is_active | BOOLEAN | 是否活跃 |
| date_joined | TIMESTAMP | 注册时间 |
| company_id | UUID | 外键，关联公司 |

中间关系表：`department_members` 用于建立用户与部门的多对多关联。

### 项目与任务相关表

#### Project (项目)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| ProjectID | INTEGER | 主键 |
| ProjectName | VARCHAR(100) | 项目名称 |
| Description | TEXT | 项目描述 |
| StartDate | DATE | 开始日期 |
| EndDate | DATE | 结束日期 |
| TimeZone | VARCHAR(50) | 时区 |
| KPI | VARCHAR(500) | KPI指标 |
| DailyReportURL | VARCHAR(500) | 日报链接 |
| ProductBackend | VARCHAR(200) | 产品后台 |
| ManagerID | UUID | 外键，关联项目负责人 |
| CompanyID | UUID | 外键，关联公司 |
| TaskTypeID | INTEGER | 外键，关联任务类型 |
| MediaChannelID | INTEGER | 外键，关联媒体渠道 |
| Status | VARCHAR(20) | 项目状态 |
| Status2ID | INTEGER | 外键，关联项目状态2 |

#### TaskType (任务类型)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| TaskTypeID | INTEGER | 主键 |
| TaskTypeName | VARCHAR(100) | 类型名称 |
| Description | TEXT | 类型描述 |
| CompanyID | UUID | 外键，关联公司 |

#### MediaChannel (媒体渠道)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| MediaChannelID | INTEGER | 主键 |
| MediaChannelName | VARCHAR(100) | 渠道名称 |
| Description | TEXT | 渠道描述 |
| CompanyID | UUID | 外键，关联公司 |

#### TaskStatus (任务状态)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| TaskStatusID | INTEGER | 主键 |
| TaskStatusName | VARCHAR(100) | 状态名称 |
| Description | TEXT | 状态描述 |
| CompanyID | UUID | 外键，关联公司 |

#### Task (任务)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(200) | 任务名称 |
| advert_name | VARCHAR(200) | 广告命名 |
| project_id | INTEGER | 外键，关联项目 |
| product_info | TEXT | 产品信息 |
| status_id | INTEGER | 外键，关联任务状态 |
| backend | VARCHAR(500) | 产品后台 |
| created_at | TIMESTAMP | 创建时间 |
| start_date | DATE | 开始日期 |
| end_date | DATE | 结束日期 |
| notes | TEXT | 备注信息 |
| pixel | TEXT | 广告像素 |
| publish_url | VARCHAR(500) | 投放链接 |
| company_id | UUID | 外键，关联公司 |
| timezone | VARCHAR(50) | 时区 |

中间关系表：`task_optimizer` 用于建立任务与优化师的多对多关联。

### 消耗记录相关表

#### TaskConsumption (任务消耗)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| task_id | UUID | 外键，关联任务 |
| creator_id | UUID | 外键，关联创建人 |
| date | DATE | 日期 |
| daily_consumption | DECIMAL(10,2) | 当日消耗 |
| return_flow | DECIMAL(10,2) | 回流 |
| actual_consumption | DECIMAL(10,2) | 实际消耗 |
| registrations | INTEGER | 注册人数 |
| first_deposits | INTEGER | 首充人数 |
| impressions | INTEGER | 展示量 |
| clicks | INTEGER | 点击量 |
| return_flow_ratio | DECIMAL(5,2) | 回流占比 |
| click_conversion_rate | DECIMAL(5,2) | 点击转化率 |
| registration_conversion_rate | DECIMAL(5,2) | 注册转化率 |
| registration_cost | DECIMAL(10,2) | 注册成本 |
| first_deposit_conversion_rate | DECIMAL(5,2) | 首充转化率 |
| first_deposit_cost | DECIMAL(10,2) | 首充成本 |
| click_cost | DECIMAL(10,2) | 点击成本 |
| ecpm | DECIMAL(10,2) | ECPM |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 数据库约束与索引

### 主要约束

1. **外键约束**：确保数据的引用完整性
   - 任务引用项目
   - 消耗记录引用任务
   - 部门引用公司
   - 用户引用公司

2. **唯一约束**：
   - 公司编号唯一
   - 用户名唯一
   - 项目中的部门编号唯一

3. **检查约束**：
   - 结束日期必须晚于开始日期
   - 金额字段不能为负数（除了回流可为负）

### 主要索引

1. **主键索引**：每个表的主键字段
2. **外键索引**：所有外键字段
3. **查询优化索引**：
   - 任务表上的项目ID索引
   - 消耗记录表上的日期索引
   - 消耗记录表上的任务ID和日期的联合索引

## 数据库优化策略

1. **连接池配置**：
   - 连接最大存活时间：60秒
   - 连接超时时间：10秒
   - TCP保活设置：启用

2. **查询优化**：
   - 对频繁查询条件建立适当索引
   - 复杂统计查询使用物化视图

3. **事务处理**：
   - 默认关闭自动事务（ATOMIC_REQUESTS = False）
   - 在需要的视图函数中显式使用事务

4. **数据库配置**：
   - 客户端编码：UTF8
   - 应用名称：django

## 数据库迁移管理

系统使用Django的迁移框架管理数据库结构变更。迁移文件存储在各应用的migrations目录中。执行迁移的主要命令是：

```bash
python manage.py makemigrations  # 生成迁移文件
python manage.py migrate         # 应用迁移
```

升级数据库时，建议按以下步骤操作：

1. 备份数据库
2. 创建迁移文件
3. 在测试环境验证迁移
4. 应用迁移到生产环境

## 数据备份策略

1. **定期完整备份**：每周一次完整数据库备份
2. **增量备份**：每天进行一次增量备份
3. **事务日志备份**：每小时备份一次事务日志
4. **备份验证**：定期测试备份恢复，确保备份有效

备份文件应存储在多个物理隔离的位置，包括本地存储和云端存储。 