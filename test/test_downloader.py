#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app.stock_downloader import StockDownloader

@pytest.fixture
def stock_downloader():
    """创建股票下载器实例的fixture"""
    return StockDownloader()

@pytest.mark.asyncio
async def test_get_stock_historical_data(stock_downloader):
    """测试获取单只股票的历史数据"""
    # 测试单只股票下载
    df = await stock_downloader.get_stock_historical_data('302132', '2015-01-01', '2025-12-13')
    
    # 断言返回的数据不为空
    assert not df.empty
    # 断言数据包含必要的列
    assert all(col in df.columns for col in ['date', 'open', 'close', 'high', 'low', 'amount', 'stock_code'])
    # 断言股票代码正确
    assert df['stock_code'].iloc[0] == '302132'

@pytest.mark.asyncio
async def test_search_stocks(stock_downloader):
    """测试搜索股票功能"""
    # 测试搜索股票功能
    search_result = await stock_downloader.search_stocks('茅台')
    
    # 断言返回的结果是列表类型
    assert isinstance(search_result, list)

@pytest.mark.asyncio
async def test_get_stock_info(stock_downloader):
    """测试获取股票信息功能"""
    # 测试获取股票信息功能
    stock_info = await stock_downloader.get_stock_info('600519.SH')
    
    assert stock_info is not None
    # 断言返回的结果是StockInfo类型或None
    if stock_info:
        assert hasattr(stock_info, 'symbol')
        assert hasattr(stock_info, 'name')
        assert hasattr(stock_info, 'price')
        assert stock_info.symbol == '600519.SH'
