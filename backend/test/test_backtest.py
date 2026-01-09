#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试K线形态回测功能
"""

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.backtest import backtest_kline_patterns
from app.db.stock_history import get_history
from app.pattern_dector import PatternDector
from app.db.companies import get_companies


def test_patterns(show_patterns=20, stock_code=None, patterns=None):
    """测试所有K线形态并按形态分组统计结果
    
    Args:
        show_patterns: 显示的形态统计条数，默认20条
        stock_code: 股票代码，默认None（回测所有股票）
        patterns: 要测试的形态列表，默认None（测试所有形态）
    """
    print("=== 测试所有K线形态并按形态分组统计 ===")
    
    # 确定要回测的股票列表
    if stock_code:
        stock_codes = [stock_code]
    else:
        print("\n获取所有股票代码...")
        stock_codes = get_companies()
        print(f"共找到 {len(stock_codes)} 只股票")
    
    # 遍历所有股票进行回测
    for idx, code in enumerate(stock_codes, 1):
        print(f"\n{'='*130}")
        print(f"正在回测第 {idx}/{len(stock_codes)} 只股票: {code}")
        print(f"{'='*130}")
        
        # 从数据库获取数据
        print(f"\n1. 从数据库获取 {code} 的历史数据...")
        stock_data = get_history(code, "2015-01-01", "2025-12-31")
        
        if not stock_data:
            print(f"   股票 {code} 无历史数据，跳过")
            continue
        
        print(f"   成功获取 {len(stock_data)} 条历史数据")
        
        # 执行回测 - 测试所有形态或指定形态
        print(f"\n2. 执行K线形态回测...")
        results = backtest_kline_patterns(stock_data, patterns)  # patterns为None时测试所有形态
        
        # 输出总体回测结果
        print(f"\n3. 总体回测结果：")
        print(f"总交易次数: {results['total_trades']}")
        print(f"盈利交易次数: {results['winning_trades']}")
        print(f"胜率: {results['win_rate']}%")
        print(f"总收益: {results['total_profit']}%")
        
        # 按形态分组统计结果
        if results['backtest_results']:
            print(f"\n4. 按形态分组统计结果：")
            
            # 创建PatternDector实例以获取形态中文名称映射
            # 从stock_data提取所需数据
            df = pd.DataFrame(stock_data)
            pd_instance = PatternDector(df['open'].values, df['high'].values, df['low'].values, df['close'].values, df['amount'].values)
            
            # 按形态分组
            pattern_stats = {}
            for trade in results['backtest_results']:
                pattern_code = trade['pattern']
                chinese_name = trade['chinese_name']
                
                if pattern_code not in pattern_stats:
                    pattern_stats[pattern_code] = {
                        'chinese_name': chinese_name,
                        'total_trades': 0,
                        'winning_trades': 0,
                        'total_profit': 0.0,
                        'max_profit': float('-inf'),
                        'min_profit': float('inf')
                    }
                
                # 更新统计数据
                pattern_stats[pattern_code]['total_trades'] += 1
                if trade['profit_ratio'] > 0:
                    pattern_stats[pattern_code]['winning_trades'] += 1
                pattern_stats[pattern_code]['total_profit'] += trade['profit_ratio']
                if trade['profit_ratio'] > pattern_stats[pattern_code]['max_profit']:
                    pattern_stats[pattern_code]['max_profit'] = trade['profit_ratio']
                if trade['profit_ratio'] < pattern_stats[pattern_code]['min_profit']:
                    pattern_stats[pattern_code]['min_profit'] = trade['profit_ratio']
            
            # 计算胜率和平均收益
            for pattern_code in pattern_stats:
                stats = pattern_stats[pattern_code]
                stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100 if stats['total_trades'] > 0 else 0
                stats['avg_profit'] = stats['total_profit'] / stats['total_trades'] if stats['total_trades'] > 0 else 0
            
            # 按平均收益率倒排，输出指定数量的形态
            sorted_patterns = sorted(pattern_stats.items(), key=lambda x: x[1]['avg_profit'], reverse=True)
            
            # 调整表格格式，确保对齐
            print("-" * 130)
            print(f"{'形态':<18} {'形态代码':<22} {'交易次数':<10} {'盈利次数':<10} {'胜率':<10} {'平均收益':<12} {'总收益':<12} {'最大收益':<12} {'最小收益':<12}")
            print("-" * 130)
            
            display_count = min(show_patterns, len(sorted_patterns))
            for i, (pattern_code, stats) in enumerate(sorted_patterns[:display_count]):
                print(f"{stats['chinese_name']:<18} {pattern_code:<22} {stats['total_trades']:<10} {stats['winning_trades']:<10} {stats['win_rate']:>8.2f}% {stats['avg_profit']:>10.2f}% {stats['total_profit']:>10.2f}% {stats['max_profit']:>10.2f}% {stats['min_profit']:>10.2f}%")
            
            if len(sorted_patterns) > show_patterns:
                print(f"... 还有 {len(sorted_patterns) - show_patterns} 种形态未显示")
        else:
            print(f"\n4. 未检测到任何形态信号")
    
    print(f"\n{'='*130}")
    print(f"=== 回测完成，共回测 {len(stock_codes)} 只股票 ===")
    print(f"{'='*130}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='K线形态回测测试工具')
    parser.add_argument('--stock', type=str, default=None, help='股票代码，不指定则回测所有股票')
    parser.add_argument('--patterns', type=str, nargs='+', help='要测试的形态列表，不指定则测试所有形态')
    parser.add_argument('--show-patterns', type=int, default=20, help='显示的形态统计条数，默认20条')
    
    args = parser.parse_args()
    
    test_patterns(show_patterns=args.show_patterns, stock_code=args.stock, patterns=args.patterns)

