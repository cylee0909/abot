import talib
import pandas as pd
import inspect
from typing import List, Dict, Any
from .pattern_dector import PatternDector

def detect_kline_patterns(stock_data: List[Dict[str, Any]], patterns: List[str] = None) -> Dict[str, Any]:
    """
    使用TA-Lib检测K线形态
    :param stock_data: 股票历史数据，包含date, open, close, high, low, amount字段
    :param patterns: 要检测的K线形态列表，如["CDL2CROWS", "CDL3BLACKCROWS"]，默认检测所有形态
    :return: 包含检测结果的字典
    """
    if not stock_data:
        return {"patterns": [], "latest_date": None}
    
    # 转换为DataFrame
    df = pd.DataFrame(stock_data)
    
    # 提取所需字段并转换为double类型（浮点数）
    open_prices = df['open'].astype(float).values
    high_prices = df['high'].astype(float).values
    low_prices = df['low'].astype(float).values
    close_prices = df['close'].astype(float).values
    dates = df['date'].values
    
    # 提取成交量数据（如果存在）
    volume = df['amount'].astype(float).values if 'amount' in df.columns else None
    
    # 初始化结果字典
    results = {
        "latest_date": dates[-1] if len(dates) > 0 else None,
        "patterns": []
    }
    
    # 创建 PatternMap 实例
    if volume is None:
        # 如果没有成交量数据，使用默认值0
        volume = [0] * len(open_prices)
    pattern_dector = PatternDector(open_prices, high_prices, low_prices, close_prices, volume)
    
    # 检测所有K线形态
    pattern_results = pattern_dector.detect_patterns(patterns)
    if not pattern_results:
        return {"patterns": [], "latest_date": None}

    # 遍历结果，找到所有出现的K线形态
    for pattern_name, pattern_result in pattern_results.items():
        # 遍历结果，找到所有出现的K线形态
        for i, result in enumerate(pattern_result):
            if result != 0:  # 0表示没有形态，正数表示看涨，负数表示看跌
                # 添加到结果列表
                results["patterns"].append({
                    "date": dates[i],
                    "pattern": pattern_name,
                    "chinese_name": pattern_dector.get_pattern_chinese_name(pattern_name),
                    "value": int(result),
                    "direction": "bullish" if result > 0 else "bearish"
                })
    
    return results