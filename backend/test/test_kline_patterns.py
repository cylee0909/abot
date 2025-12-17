import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

# 测试K线形态检测函数
def test_kline_patterns_function():
    """直接测试K线形态检测函数，使用真实数据库数据"""
    from app.kline_patterns import detect_kline_patterns, detect_latest_patterns
    from app.db.stock_history import get_history
    
    print("\n直接测试K线形态检测函数（使用真实数据库数据）")
    
    try:
        # 从数据库获取真实股票数据，例如贵州茅台(600519)
        stock_code = "600519"
        limit = 100  # 获取最近100条数据
        
        print(f"正在从数据库获取股票 {stock_code} 的历史数据...")
        history_data = get_history(stock_code, limit=limit)
        
        if not history_data:
            print(f"未获取到股票 {stock_code} 的历史数据")
            return False
        
        print(f"成功获取到 {len(history_data)} 条历史数据，时间范围：{history_data[0]['date']} 到 {history_data[-1]['date']}")
        
        # 测试1：检测所有形态
        print("\n1. 检测所有K线形态：")
        results_all = detect_kline_patterns(history_data)
        print(f"检测到的K线形态总数：{len(results_all.get('patterns', []))}")
        
        if results_all.get('patterns'):
            # 打印前10个检测结果
            print("前10个检测结果：")
            for i, pattern in enumerate(results_all['patterns'][:10]):
                print(f"{i+1}. 日期：{pattern['date']}, 形态：{pattern['pattern']}, 方向：{pattern['direction']}, 值：{pattern['value']}")
            if len(results_all['patterns']) > 10:
                print(f"... 共 {len(results_all['patterns'])} 个结果")
        
        # 测试2：检测指定形态
        print("\n2. 检测指定K线形态（CDLDOJI, CDLHAMMER, CDLHANGINGMAN）：")
        target_patterns = ["CDLDOJI", "CDLHAMMER", "CDLHANGINGMAN"]
        results_specific = detect_kline_patterns(history_data, patterns=target_patterns)
        print(f"检测到的指定形态总数：{len(results_specific.get('patterns', []))}")
        
        if results_specific.get('patterns'):
            for pattern in results_specific['patterns']:
                print(f"日期：{pattern['date']}, 形态：{pattern['pattern']}, 方向：{pattern['direction']}, 值：{pattern['value']}")
        
        # 测试3：检测最近10天的形态
        print("\n3. 检测最近10天的K线形态：")
        results_latest = detect_latest_patterns(history_data, days=10, patterns=target_patterns)
        print(f"最近10天检测到的形态数量：{len(results_latest.get('patterns', []))}")
        
        if results_latest.get('patterns'):
            for pattern in results_latest['patterns']:
                print(f"日期：{pattern['date']}, 形态：{pattern['pattern']}, 方向：{pattern['direction']}, 值：{pattern['value']}")
        else:
            print("最近10天未检测到指定形态")
        
        return True
    except Exception as e:
        print(f"\n检测函数发生异常：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_kline_patterns_function()
    
