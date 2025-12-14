#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from src.data_updater import DataUpdater

def check_missing_stocks():
    """
    检查哪些沪深300成分股没有成功下载历史数据
    """
    # 初始化数据更新器
    updater = DataUpdater('./data/hs300_history.db')
    
    # 获取所有沪深300成分股
    all_stocks = updater.get_hs300_stocks()
    print(f"沪深300成分股总数: {len(all_stocks)}")
    
    # 连接数据库，查询已下载的股票
    conn = sqlite3.connect('./data/hs300_history.db')
    cursor = conn.cursor()
    
    # 查询已下载的股票代码列表
    cursor.execute('SELECT DISTINCT stock_code FROM stock_history')
    downloaded_stocks = [row[0] for row in cursor.fetchall()]
    print(f"已成功下载的股票数量: {len(downloaded_stocks)}")
    
    # 找出未下载的股票
    missing_stocks = list(set(all_stocks) - set(downloaded_stocks))
    missing_stocks.sort()
    
    print(f"未成功下载的股票数量: {len(missing_stocks)}")
    if missing_stocks:
        print("未成功下载的股票代码:")
        for stock in missing_stocks:
            print(f"  - {stock}")
        
        # 查询这些股票的详细信息
        print("\n未成功下载的股票详细信息:")
        for stock in missing_stocks:
            cursor.execute('SELECT security_name_abbr, industry, region FROM hs300_components WHERE security_code = ?', (stock,))
            result = cursor.fetchone()
            if result:
                name, industry, region = result
                print(f"  - {stock} {name} ({industry} - {region})")
            else:
                print(f"  - {stock} (未找到详细信息)")
    else:
        print("所有股票都已成功下载!")
    
    conn.close()

if __name__ == "__main__":
    check_missing_stocks()
