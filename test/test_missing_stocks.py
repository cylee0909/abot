#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.conponents_updater import ComponentsUpdater
from app.db import db

@pytest.fixture
def components_updater():
    """创建ComponentsUpdater实例的fixture"""
    return ComponentsUpdater('./data/hs300_history.db')

def test_check_missing_stocks(components_updater):
    """测试检查哪些公司没有成功下载历史数据"""
    # 获取所有公司
    all_stocks = components_updater.get_stocks()
    assert len(all_stocks) > 0, "公司列表为空"
    
    # 连接数据库，查询已下载的股票
    cursor = db.get_cursor()
    
    # 查询已下载的股票代码列表
    cursor.execute('SELECT DISTINCT stock_code FROM stock_history')
    downloaded_stocks = [row[0] for row in cursor.fetchall()]
    
    # 找出未下载的股票
    missing_stocks = list(set(all_stocks) - set(downloaded_stocks))
    
    # 打印结果（用于调试，实际测试中可以注释掉）
    print(f"公司总数: {len(all_stocks)}")
    print(f"已成功下载的股票数量: {len(downloaded_stocks)}")
    print(f"未成功下载的股票数量: {len(missing_stocks)}")
    
    # 断言已下载的股票数量大于0
    assert len(downloaded_stocks) > 0, "没有成功下载的股票"
    
    # 可以根据实际需求添加更多断言
    # 例如：断言未下载的股票数量不超过某个阈值
    # assert len(missing_stocks) < len(all_stocks) * 0.1, "未下载的股票数量过多"
    
    # 打印未下载的股票（用于调试）
    if missing_stocks:
        print("未成功下载的股票代码:")
        for stock in sorted(missing_stocks):
            print(f"  - {stock}")
    else:
        print("所有股票都已成功下载!")

def test_check_missing_stocks_details(components_updater):
    """测试检查未下载股票的详细信息"""
    # 获取所有公司
    all_stocks = components_updater.get_stocks()
    assert len(all_stocks) > 0, "公司列表为空"
    
    # 连接数据库，查询已下载的股票
    cursor = db.get_cursor()
    
    # 查询已下载的股票代码列表
    cursor.execute('SELECT DISTINCT stock_code FROM stock_history')
    downloaded_stocks = [row[0] for row in cursor.fetchall()]
    
    # 找出未下载的股票
    missing_stocks = list(set(all_stocks) - set(downloaded_stocks))
    
    # 如果有未下载的股票，检查它们的详细信息
    if missing_stocks:
        for stock in sorted(missing_stocks):
            cursor.execute('SELECT security_name_abbr, industry, region FROM components WHERE security_code = ?', (stock,))
            result = cursor.fetchone()
            # 断言每个未下载的股票都能在成分股表中找到详细信息
            assert result is not None, f"股票 {stock} 在成分股表中未找到详细信息"
            name, industry, region = result
            print(f"  - {stock} {name} ({industry} - {region})")
