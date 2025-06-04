#!/usr/bin/env python
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 添加Django项目路径到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ad_manplat.settings')

# 导入Django设置
import django
django.setup()
from django.conf import settings

def reset_sequences():
    """重置PostgreSQL数据库中的所有序列值"""
    # 从Django设置中获取数据库配置
    db_settings = settings.DATABASES['default']
    
    # 连接到数据库
    conn = psycopg2.connect(
        dbname=db_settings['NAME'],
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        host=db_settings['HOST'],
        port=db_settings['PORT']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    cursor = conn.cursor()
    print("已连接到数据库:", db_settings['NAME'])

    try:
        # 查询所有序列和它们关联的表和列
        cursor.execute("""
            SELECT
                n.nspname as 表模式,
                c.relname as 表名,
                a.attname as 列名,
                s.relname as 序列名
            FROM pg_class s
            JOIN pg_depend d ON d.objid = s.oid
            JOIN pg_class c ON c.oid = d.refobjid
            JOIN pg_attribute a ON (a.attrelid = c.oid AND a.attnum = d.refobjsubid)
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE s.relkind = 'S' AND n.nspname != 'pg_catalog'
            ORDER BY n.nspname, c.relname, a.attname;
        """)
        
        sequences = cursor.fetchall()
        reset_count = 0
        
        for schema, table, column, sequence in sequences:
            # 查询表中列的最大值
            max_id_query = f'SELECT MAX("{column}") FROM "{schema}"."{table}"'
            cursor.execute(max_id_query)
            max_id = cursor.fetchone()[0]
            
            if max_id is None:
                max_id = 0
            
            # 设置序列值为最大ID + 1
            reset_query = f'ALTER SEQUENCE "{schema}"."{sequence}" RESTART WITH {max_id + 1}'
            cursor.execute(reset_query)
            reset_count += 1
            
            print(f"已重置序列 {schema}.{sequence} 为 {max_id + 1} (表: {table}, 列: {column})")
        
        print(f"成功重置了 {reset_count} 个序列")

    except Exception as e:
        print(f"错误: {e}")
    finally:
        cursor.close()
        conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    reset_sequences() 