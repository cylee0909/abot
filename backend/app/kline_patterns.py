import talib
import pandas as pd
from typing import List, Dict, Any
from .patterns_map import all_pattern_functions, pattern_chinese_names


def detect_kline_patterns(stock_data: List[Dict[str, Any]], patterns: List[str] = None) -> Dict[str, Any]:
    """
    使用TA-Lib检测K线形态
    :param stock_data: 股票历史数据，包含date, open, close, high, low字段
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
    
    # 初始化结果字典
    results = {
        "latest_date": dates[-1] if len(dates) > 0 else None,
        "patterns": []
    }
    

    
    # 根据传入的patterns参数过滤要检测的形态
    pattern_functions = []
    if patterns:
        # 如果传入了形态列表，只检测列表中的形态
        for pattern_name in patterns:
            if pattern_name in all_pattern_functions:
                pattern_functions.append((pattern_name, all_pattern_functions[pattern_name]))
            else:
                print(f"警告：形态 {pattern_name} 不存在，将被跳过")
    else:
        # 如果没有传入形态列表，检测所有形态
        pattern_functions = list(all_pattern_functions.items())
    
    # 检测每个K线形态
    for pattern_name, pattern_func in pattern_functions:
        # 调用TA-Lib函数检测K线形态
        pattern_results = pattern_func(open_prices, high_prices, low_prices, close_prices)
        
        # 遍历结果，找到所有出现的K线形态
        for i, result in enumerate(pattern_results):
            if result != 0:  # 0表示没有形态，正数表示看涨，负数表示看跌
                # 添加到结果列表
                results["patterns"].append({
                    "date": dates[i],
                    "pattern": pattern_name,
                    "chinese_name": pattern_chinese_names.get(pattern_name),
                    "value": int(result),
                    "direction": "bullish" if result > 0 else "bearish"
                })
    
    return results


def detect_latest_patterns(stock_data: List[Dict[str, Any]], days: int = 30, patterns: List[str] = None) -> Dict[str, Any]:
    """
    检测最近指定天数内的K线形态
    :param stock_data: 股票历史数据
    :param days: 最近天数
    :param patterns: 要检测的K线形态列表，默认检测所有形态
    :return: 包含最近检测结果的字典
    """
    # 获取检测结果
    all_results = detect_kline_patterns(stock_data, patterns)
    
    # 如果没有数据，直接返回
    if not all_results["patterns"]:
        return all_results
    
    # 只保留最近days天的结果
    latest_date = pd.to_datetime(all_results["latest_date"])
    filtered_patterns = []
    
    for pattern in all_results["patterns"]:
        pattern_date = pd.to_datetime(pattern["date"])
        # 计算日期差
        if (latest_date - pattern_date).days <= days:
            filtered_patterns.append(pattern)
    
    # 更新结果
    all_results["patterns"] = filtered_patterns
    return all_results
