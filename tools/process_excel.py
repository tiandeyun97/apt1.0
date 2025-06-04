import pandas as pd
import re

# 读取Excel文件
file_path = r"C:\Users\39306\Desktop\tasks_project - 副本.xlsx"
df = pd.read_excel(file_path)

# 1. 处理DailyReportURL列，将"edit"后面的文本替换为空
def clean_url(url):
    if isinstance(url, str):
        return re.sub(r'edit.*$', '', url)
    return url

df['DailyReportURL'] = df['DailyReportURL'].apply(clean_url)

# 2. 去除ProjectName和DailyReportURL重复的行，保持数据唯一性
df = df.drop_duplicates(subset=['ProjectName', 'DailyReportURL'])

# 保存处理后的数据到新文件
output_file = r"C:\Users\39306\Desktop\tasks_project_processed.xlsx"
df.to_excel(output_file, index=False)

print(f"数据处理完成，已保存到 {output_file}") 