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


def test_backtest(show_trades=10):
    """测试回测功能"""
    print("=== 测试K线形态回测功能 ===")
    
    # 选择一只股票进行测试
    stock_code = "600519"  # 贵州茅台
    
    # 从数据库获取数据
    print(f"\n1. 从数据库获取 {stock_code} 的历史数据...")
    stock_data = get_history(stock_code, "2015-01-01", "2025-12-31")
    
    if not stock_data:
        print("无法获取股票数据，测试失败！")
        return
    
    print(f"成功获取 {len(stock_data)} 条历史数据")
    
    # 执行回测
    print(f"\n2. 执行K线形态回测...")
    results = backtest_kline_patterns(stock_data, ["OLD_DUCK_HEAD"])
    
    # 输出回测结果
    print(f"\n3. 回测结果：")
    print(f"总交易次数: {results['total_trades']}")
    print(f"盈利交易次数: {results['winning_trades']}")
    print(f"胜率: {results['win_rate']}%")
    print(f"总收益: {results['total_profit']}%")
    
    # 输出详细交易记录
    if results['backtest_results']:
        print(f"\n4. 详细交易记录：")
        print("-" * 100)
        print(f"{'形态':<20} {'信号日期':<12} {'买入日期':<12} {'买入价格':<10} {'卖出日期':<12} {'卖出价格':<10} {'持有天数':<8} {'收益':<10} {'卖出原因':<20}")
        print("-" * 100)
        
        display_count = min(show_trades, len(results['backtest_results']))
        for trade in results['backtest_results'][:display_count]:
            print(f"{trade['chinese_name']:<20} {trade['signal_date']:<12} {trade['buy_date']:<12} {trade['buy_price']:<10} {trade['sell_date']:<12} {trade['sell_price']:<10} {trade['hold_days']:<8} {trade['profit_ratio']:<10} {trade['sell_reason']:<20}")
        
        if len(results['backtest_results']) > show_trades:
            print(f"... 还有 {len(results['backtest_results']) - show_trades} 条记录未显示")
    
    print(f"\n=== 测试完成 ===")

def test_all_patterns(show_patterns=20):
    """测试所有K线形态并按形态分组统计结果"""
    print("=== 测试所有K线形态并按形态分组统计 ===")
    
    # 选择一只股票进行测试
    stock_code = "600519"  # 贵州茅台
    
    # 从数据库获取数据
    print(f"\n1. 从数据库获取 {stock_code} 的历史数据...")
    stock_data = get_history(stock_code, "2015-01-01", "2025-12-31")
    
    if not stock_data:
        print("无法获取股票数据，测试失败！")
        return
    
    print(f"成功获取 {len(stock_data)} 条历史数据")
    
    # 执行回测 - 测试所有形态
    print(f"\n2. 执行所有K线形态回测...")
    results = backtest_kline_patterns(stock_data)  # 不指定patterns参数，默认测试所有形态
    
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
    
    print(f"\n=== 测试完成 ===")

if __name__ == "__main__":
    # 运行单个形态测试 - 可配置显示的交易记录条数，默认10条
    test_backtest()
    # 运行所有形态测试 - 可配置显示的形态统计条数，默认20条
    test_all_patterns()

