#!/usr/bin/env python3
from app.db import db

# 查询所有公司信息
cursor = db.get_cursor()
cursor.execute('SELECT security_code, security_name_abbr FROM companies ORDER BY security_name_abbr')
companies = cursor.fetchall()

total_companies = len(companies)
companies_with_data = 0

print("\n=== 公司历史数据统计 ===\n")
print(f"{'公司名称':<20} {'股票代码':<10} {'数据条数':<10} {'起始日期':<15} {'结束日期':<15}")
print("-" * 75)

for security_code, security_name in companies:
    # 查询该公司的历史数据统计
    cursor.execute('''
        SELECT COUNT(*), MIN(date), MAX(date) 
        FROM stock_history 
        WHERE stock_code = ?
    ''', (security_code,))
    count, start_date, end_date = cursor.fetchone()
    
    if count > 0:
        companies_with_data += 1
        print(f"{security_name:<20} {security_code:<10} {count:<10} {start_date:<15} {end_date:<15}")
    else:
        print(f"{security_name:<20} {security_code:<10} {count:<10} {'无数据':<15} {'无数据':<15}")

print("-" * 75)
print(f"\n=== 汇总信息 ===")
print(f"总计公司数量: {total_companies}")
print(f"有历史数据的公司数量: {companies_with_data}")
print(f"无历史数据的公司数量: {total_companies - companies_with_data}")

# 关闭数据库连接
db.close()