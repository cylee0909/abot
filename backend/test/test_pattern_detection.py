#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试K线形态检测功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.kline_patterns import detect_kline_patterns, detect_latest_patterns
from app.db.stock_history import get_history
from app.db.companies import get_companies


def test_kline_patterns_api(stock_code=None, patterns=None, show_details=10, start_time="2015-01-01", end_time="2025-12-31"):
    """测试kline_patterns模块的API
    
    Args:
        stock_code: 股票代码，默认None（检测所有股票）
        patterns: 要检测的形态列表，默认None（检测所有形态）
        show_details: 显示的详细形态数量，默认10条
        start_time: 开始日期，默认"2015-01-01"
        end_time: 结束日期，默认"2025-12-31"
    """
    print("=== 测试kline_patterns模块API ===")
    
    # 确定要检测的股票列表
    if stock_code:
        stock_codes = [stock_code]
    else:
        print("\n获取所有股票代码...")
        stock_codes = get_companies()
        print(f"共找到 {len(stock_codes)} 只股票")
    
    # 遍历所有股票进行检测
    for idx, code in enumerate(stock_codes, 1):
        print(f"\n{'='*100}")
        print(f"正在检测第 {idx}/{len(stock_codes)} 只股票: {code}")
        print(f"{'='*100}")
        
        # 从数据库获取数据
        print(f"\n1. 从数据库获取 {code} 的历史数据...")
        print(f"   时间范围: {start_time} 至 {end_time}")
        stock_data = get_history(code, start_time, end_time)
        
        if not stock_data:
            print(f"   股票 {code} 无历史数据，跳过")
            continue
        
        print(f"   成功获取 {len(stock_data)} 条历史数据")
        
        # 测试detect_kline_patterns函数
        print(f"\n2. 测试detect_kline_patterns函数...")
        results = detect_kline_patterns(stock_data, patterns)
        
        print(f"   最新日期: {results['latest_date']}")
        print(f"   检测到的形态数量: {len(results['patterns'])}")
        
        # 显示检测结果
        if results['patterns']:
            print(f"\n3. 检测到的形态：")
            print("-" * 120)
            print(f"{'形态代码':<25} {'中文名称':<20} {'日期':<12} {'信号值':<8} {'方向':<10}")
            print("-" * 120)
            
            display_count = min(show_details, len(results['patterns']))
            for i, pattern in enumerate(results['patterns'][:display_count]):
                print(f"{pattern['pattern']:<25} {pattern['chinese_name']:<20} {pattern['date']:<12} {pattern['value']:<8} {pattern['direction']:<10}")
            
            if len(results['patterns']) > show_details:
                print(f"... 还有 {len(results['patterns']) - show_details} 条记录未显示")
        else:
            print(f"\n3. 未检测到任何形态")
    
    print(f"\n{'='*100}")
    print(f"=== 测试完成，共检测 {len(stock_codes)} 只股票 ===")
    print(f"{'='*100}")


if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='K线形态检测测试工具')
    parser.add_argument('--stock', type=str, default=None, help='股票代码，不指定则检测所有股票')
    parser.add_argument('--patterns', type=str, nargs='+', help='要测试的形态列表，不指定则测试所有形态')
    parser.add_argument('--show-details', type=int, default=10, help='显示的详细数量，默认10条')
    parser.add_argument('--start', type=str, default="2015-01-01", help='开始日期，默认"2015-01-01"')
    parser.add_argument('--end', type=str, default=datetime.now().strftime("%Y-%m-%d"), help='结束日期，默认今天')
    
    args = parser.parse_args()
    
    test_kline_patterns_api(stock_code=args.stock, patterns=args.patterns, show_details=args.show_details, start_time=args.start, end_time=args.end)
