import pandas as pd
from pypinyin import lazy_pinyin
import re

# 读取已处理好的Excel文件
processed_file_path = r"C:\Users\39306\Desktop\tasks_project.xlsx"
df_processed = pd.read_excel(processed_file_path)

print(f"已读取处理好的文件: {processed_file_path}")
print(f"处理好的文件中的列名: {df_processed.columns.tolist()}")

# 读取需要填充的Excel文件
target_file_path = r"C:\Users\39306\Desktop\task_import_template(1).xlsx"
df_target = pd.read_excel(target_file_path)

print(f"已读取目标文件: {target_file_path}")
print(f"目标文件中的列名: {df_target.columns.tolist()}")

# 创建详细的项目信息映射
project_data = {}

# 遍历处理好的文件，建立详细映射
for idx, row in df_processed.iterrows():
    project_name = row.get('ProjectName', None)  
    project_id = row.get('ProjectID', None)
    media_channel_id = row.get('MediaChannelID_id', None)
    task_type_id = row.get('TaskTypeID_id', None)
    
    if pd.notna(project_name) and pd.notna(project_id):
        # 使用项目名称作为键，存储完整的相关数据
        if str(project_name) not in project_data:
            project_data[str(project_name)] = []
        
        # 添加这条记录的所有相关信息
        project_data[str(project_name)].append({
            'project_id': project_id,
            'media_channel_id': media_channel_id,
            'task_type_id': task_type_id
        })

print(f"已创建项目信息映射，共有 {len(project_data)} 个不同的项目名称")

# 从任务名称中提取渠道和任务类型
def extract_channel_and_type(task_name):
    # 匹配格式如 "310005-FB-H5-04"
    pattern = r'[\d\w]+-(\w+)-(\w+)-[\d\w]+'
    match = re.match(pattern, str(task_name))
    
    if match:
        channel = match.group(1)  # 例如 "FB"
        task_type = match.group(2)  # 例如 "H5"
        return channel, task_type
    
    return None, None

# 函数：将中文转换为拼音首字母
def chinese_to_uppercase_pinyin(text):
    if pd.isna(text):
        return text
    
    # 只处理中文字符
    if re.search(r'[\u4e00-\u9fff]', str(text)):
        # 转换为拼音列表
        pinyin_list = lazy_pinyin(str(text))
        # 只保留每个拼音的首字母并大写
        initials = ''.join([word[0].upper() for word in pinyin_list if word])
        return initials
    else:
        # 如果是英文，则全部转为大写
        return str(text).upper()

# 处理可能包含多个优化师的情况
def process_optimizer_names(optimizer_text):
    if pd.isna(optimizer_text):
        return optimizer_text
    
    # 同时处理英文逗号和中文逗号
    delimiter = None
    if ',' in str(optimizer_text):
        delimiter = ','
    elif '，' in str(optimizer_text):
        delimiter = '，'
    
    # 如果找到分隔符，分别处理每个名字
    if delimiter:
        names = str(optimizer_text).split(delimiter)
        processed_names = [chinese_to_uppercase_pinyin(name.strip()) for name in names]
        return delimiter.join(processed_names)
    else:
        # 单个名字的情况
        return chinese_to_uppercase_pinyin(optimizer_text)

# 计数器
matched_count = 0
not_found_count = 0

# 为目标Excel填充项目ID
project_id_column = "项目ID*"
project_name_column = "项目名称"
task_name_column = "任务名称"  # 假设存在这个列
optimizer_column = "优化师"  # 优化师列名

print("开始填充项目ID和转换优化师名称...")

# 处理Excel数据
for idx, row in df_target.iterrows():
    # 1. 填充项目ID
    project_name = row.get(project_name_column)
    task_name = row.get(task_name_column, None)
    
    if pd.notna(project_name):
        project_name_str = str(project_name)
        
        # 从任务名称中提取渠道和类型
        channel, task_type = None, None
        if pd.notna(task_name):
            channel, task_type = extract_channel_and_type(task_name)
            if channel and task_type:
                print(f"行 {idx+2}: 从任务名称 '{task_name}' 提取到渠道 '{channel}' 和任务类型 '{task_type}'")
        
        # 检查项目名称是否在映射中
        if project_name_str in project_data:
            # 获取该项目名称的所有记录
            project_records = project_data[project_name_str]
            
            # 如果有多条记录且提取到了渠道和任务类型，尝试精确匹配
            if len(project_records) > 1 and channel and task_type:
                # 尝试找到渠道和任务类型都匹配的记录
                for record in project_records:
                    media_match = (str(record['media_channel_id']).upper() == channel.upper())
                    type_match = (str(record['task_type_id']).upper() == task_type.upper())
                    
                    if media_match and type_match:
                        df_target.at[idx, project_id_column] = record['project_id']
                        print(f"行 {idx+2}: 精确匹配找到项目 '{project_name_str}' 的ID: {record['project_id']} (渠道: {channel}, 类型: {task_type})")
                        matched_count += 1
                        break
                else:  # 如果没有精确匹配
                    # 使用第一条记录
                    df_target.at[idx, project_id_column] = project_records[0]['project_id']
                    print(f"行 {idx+2}: 未找到精确匹配，使用项目 '{project_name_str}' 的第一个ID: {project_records[0]['project_id']}")
                    matched_count += 1
            else:
                # 只有一条记录或无法提取渠道和类型，使用第一条
                df_target.at[idx, project_id_column] = project_records[0]['project_id']
                print(f"行 {idx+2}: 使用项目 '{project_name_str}' 的ID: {project_records[0]['project_id']}")
                matched_count += 1
        else:
            print(f"行 {idx+2}: 未找到项目 '{project_name_str}' 的任何记录")
            not_found_count += 1
    
    # 2. 处理优化师列，将中文名转为大写拼音
    if optimizer_column in df_target.columns:
        optimizer_name = row.get(optimizer_column)
        if pd.notna(optimizer_name):
            processed_name = process_optimizer_names(optimizer_name)
            if processed_name != optimizer_name:
                df_target.at[idx, optimizer_column] = processed_name
                print(f"行 {idx+2}: 优化师 '{optimizer_name}' 转换为 '{processed_name}'")

# 保存结果
output_file = r"C:\Users\39306\Desktop\task_import_template_filled.xlsx"
df_target.to_excel(output_file, index=False)

print(f"处理完成，共有 {matched_count} 行成功匹配项目ID，{not_found_count} 行未匹配")
print(f"优化师名称已转换为首字母缩写")
print(f"已保存到 {output_file}") 