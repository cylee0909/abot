#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from datetime import datetime, timedelta
from src.stock_downloader import StockDownloader

async def test_downloader():
    """
    测试股票下载器
    """
    downloader = StockDownloader()
    
    # 测试单只股票下载
    print("测试单只股票下载...")
    df = await downloader.get_stock_historical_data('302132', '2015-01-01', '2025-12-13')
    print(f"获取到 {len(df)} 条302132历史数据")
    if not df.empty:
        print(df.head())
    
    # 测试搜索股票功能
    print("\n测试搜索股票功能...")
    search_result = await downloader.search_stocks('茅台')
    print(f"搜索到 {len(search_result)} 条匹配结果")
    for stock in search_result[:5]:
        print(f"  - {stock.symbol}: {stock.name} ({stock.exchange})")
    
    # 测试获取股票信息功能
    print("\n测试获取股票信息功能...")
    stock_info = await downloader.get_stock_info('600519.SH')
    if stock_info:
        print(f"股票代码: {stock_info.symbol}")
        print(f"股票名称: {stock_info.name}")
        print(f"最新价格: {stock_info.price}")
        print(f"涨跌幅: {stock_info.changePercent}%")
        print(f"成交量: {stock_info.volume}")
        print(f"市盈率: {stock_info.pe}")
    else:
        print("未获取到股票信息")


if __name__ == "__main__":
    asyncio.run(test_downloader())
