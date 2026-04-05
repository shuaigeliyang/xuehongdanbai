"""
快速分析两个实验数据集
"""
import pandas as pd
import os

# 读取两个文件
files = [
    '实验记录-20250731.xlsx',
    '实验记录-20250812.xlsx'
]

for file in files:
    if os.path.exists(file):
        df = pd.read_excel(file)
        print('\n' + '='*60)
        print(f'文件: {file}')
        print('='*60)
        print(f'总行数: {len(df)}')
        print(f'列名: {list(df.columns)}')
        print('\n前20行数据:')
        print(df.head(20).to_string())

        # 统计信息
        print('\n数据类型:')
        print(df.dtypes)

        # 尝试识别数值列
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        print(f'\n数值列: {numeric_cols}')

        for col in numeric_cols:
            print(f'\n{col} 统计:')
            print(f'  唯一值数: {df[col].nunique()}')
            print(f'  范围: {df[col].min():.4f} - {df[col].max():.4f}')
            print(f'  均值: {df[col].mean():.4f}')
            if df[col].nunique() <= 20:
                print(f'  唯一值: {sorted(df[col].dropna().unique())}')
    else:
        print(f'\n文件不存在: {file}')

print('\n' + '='*60)
print('分析完成！')
print('='*60)
