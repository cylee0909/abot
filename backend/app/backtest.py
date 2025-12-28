import pandas as pd
from typing import List, Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
from .kline_patterns import detect_kline_patterns
from .position_manager import PositionManager


class Strategy(ABC):
    """
    交易策略抽象基类
    """
    
    def __init__(self, max_observe_days: int = 14):
        """
        初始化策略
        :param max_observe_days: 最大观察天数
        """
        self.max_observe_days = max_observe_days
    
    @abstractmethod
    def tick(self, date: pd.Timestamp, day_offset: int, open_price: float, close_price: float, volume: float):
        """
        每日行情回调
        :param date: 当日日期
        :param day_offset: 形态出现后第几日（从1开始）
        :param open_price: 当日开盘价
        :param close_price: 当日收盘价
        :param volume: 当日成交量
        """
        pass

class DefaultStrategy(Strategy):
    """
    默认交易策略
    """

    def __init__(self, stock_code: str = "default", max_observe_days: int = 14, take_profit_ratio: float = 8.0, stop_loss_ratio: float = -5.0):
        """
        初始化默认策略
        :param stock_code: 股票代码
        :param max_observe_days: 最大观察天数
        :param take_profit_ratio: 止盈比例（%）
        :param stop_loss_ratio: 止损比例（%）
        """
        super().__init__(max_observe_days)
        self.stock_code = stock_code
        self.take_profit_ratio = take_profit_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.position_manager = PositionManager()
        self.has_bought = False
        # 记录交易信息
        self.buy_date = None
        self.buy_price = 0.0
        self.sell_date = None
        self.sell_price = 0.0
        self.hold_days = 0

    
    def tick(self, date: pd.Timestamp, day_offset: int, open_price: float, close_price: float, volume: float):
        """
        每日行情回调
        :param date: 当日日期
        :param day_offset: 形态出现后第几日（从1开始）
        :param open_price: 当日开盘价
        :param close_price: 当日收盘价
        :param volume: 当日成交量
        :return: 卖出原因，如果返回None则继续持有
        """
        # 如果尚未买入，执行买入操作
        if not self.has_bought:
            # 使用开盘价全仓买入
            try:
                # 计算最大可买数量：可用现金 / 开盘价，向下取整
                available_cash = self.position_manager.available_cash
                if available_cash <= 0:
                    return "可用现金不足"
                
                # 全仓买入，数量向下取整
                quantity = int(available_cash / open_price)
                if quantity <= 0:
                    return "无法买入：价格过高"
                
                # 执行买入
                self.position_manager.buy(self.stock_code, open_price, quantity, f"day_{day_offset}")
                self.has_bought = True
                # 记录买入信息
                self.buy_date = date
                self.buy_price = open_price
                return None  # 继续持有
            except ValueError as e:
                # 资金不足，无法买入
                return f"无法买入: {str(e)}"
        
        # 更新当前价格
        self.position_manager.update_current_price(self.stock_code, close_price)
        
        # 获取当前持仓
        position = self.position_manager.get_position(self.stock_code)
        if not position:
            return "持仓已清空"
        
        # 计算当前盈亏比例
        avg_buy_price = position["avg_price"]
        profit_ratio = (close_price - avg_buy_price) / avg_buy_price * 100
        
        # 1. 检查是否达到最大观察天数
        if day_offset >= self.max_observe_days:
            # 卖出所有持仓
            self.position_manager.sell(self.stock_code, close_price, position["quantity"], f"day_{day_offset}")
            # 记录卖出信息
            self.sell_date = date
            self.sell_price = close_price
            self.hold_days = day_offset
            return f"达到最大观察天数 {self.max_observe_days} 天"
        
        # 2. 检查止盈条件
        if profit_ratio >= self.take_profit_ratio:
            # 卖出所有持仓
            self.position_manager.sell(self.stock_code, close_price, position["quantity"], f"day_{day_offset}")
            # 记录卖出信息
            self.sell_date = date
            self.sell_price = close_price
            self.hold_days = day_offset
            return f"达到止盈比例 {self.take_profit_ratio}%"
        
        # 3. 检查止损条件
        if profit_ratio <= self.stop_loss_ratio:
            # 卖出所有持仓
            self.position_manager.sell(self.stock_code, close_price, position["quantity"], f"day_{day_offset}")
            # 记录卖出信息
            self.sell_date = date
            self.sell_price = close_price
            self.hold_days = day_offset
            return f"达到止损比例 {self.stop_loss_ratio}%"

        # 继续持有
        return None
    
    def get_backtest_result(self):
        """
        获取回测结果
        :return: 回测结果字典
        """
        # 计算盈亏
        profit = self.sell_price - self.buy_price
        profit_ratio = (profit / self.buy_price) * 100 if self.buy_price > 0 else 0
        
        return {
            "buy_date": self.buy_date,
            "buy_price": self.buy_price,
            "sell_date": self.sell_date,
            "sell_price": self.sell_price,
            "hold_days": self.hold_days,
            "profit": profit,
            "profit_ratio": profit_ratio
        }

def backtest_kline_patterns(stock_data: List[Dict[str, Any]], patterns: List[str] = None, strategy_creator: Optional[Callable[[str], Strategy]] = None) -> Dict[str, Any]:
    """
    对K线形态进行回测
    :param stock_data: 股票历史数据，包含date, open, close, high, low, amount字段
    :param patterns: 要检测的K线形态列表，如["CDL2CROWS", "CDL3BLACKCROWS"]，默认检测所有形态
    :param strategy_creator: 交易策略创建函数，默认使用DefaultStrategy
    :return: 包含回测结果的字典
    """
    
    if not stock_data:
        return {"backtest_results": [], "total_trades": 0, "winning_trades": 0, "win_rate": 0, "total_profit": 0}
    
    # 转换为DataFrame
    df = pd.DataFrame(stock_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # 数据验证：过滤掉价格为负数或零的记录
    df = df[(df['open'] > 0) & (df['close'] > 0) & (df['high'] > 0) & (df['low'] > 0)]
    
    if len(df) < 30:  # 至少需要30天的数据才能进行回测
        return {"backtest_results": [], "total_trades": 0, "winning_trades": 0, "win_rate": 0, "total_profit": 0}
    
    # 转换回列表字典格式，用于检测K线形态
    valid_stock_data = df.to_dict('records')
    
    # 检测所有K线形态
    detection_results = detect_kline_patterns(valid_stock_data, patterns)
    
    print(f"检测到 {len(detection_results['patterns'])} 个K线形态")
    
    if not detection_results["patterns"]:
        return {"backtest_results": [], "total_trades": 0, "winning_trades": 0, "win_rate": 0, "total_profit": 0}
    
    # 提取看涨形态
    bullish_patterns = [p for p in detection_results["patterns"] if p["direction"] == "bullish"]
    
    backtest_results = []
    total_trades = 0
    winning_trades = 0
    total_profit = 0.0

    print(f"检测到 {len(bullish_patterns)} 个看涨形态")
    for pattern in bullish_patterns:
        # 找到形态出现的日期在df中的索引
        pattern_date = pd.to_datetime(pattern["date"])
        pattern_idx = df[df['date'] == pattern_date].index
        
        if not len(pattern_idx):
            continue
        
        strategy = strategy_creator(pattern["pattern"]) if strategy_creator else DefaultStrategy()

        pattern_idx = pattern_idx[0]
        
        # 确保有足够的历史数据和未来数据
        buy_idx = pattern_idx 
        # 模拟持有期间，检查卖出条件
        for i in range(buy_idx + 1, buy_idx + strategy.max_observe_days + 1):
            if i >= len(df):
                break
                
            # 获取当日行情数据
            current_row = df.iloc[i]
            day_offset = i - buy_idx  # 形态出现后第几日
            open_price = current_row['open']
            close_price = current_row['close']
            volume = current_row['amount']
            
            # 跳过无效的价格
            if open_price <= 0 or close_price <= 0:
                continue
            
            # 调用策略的tick方法判断是否卖出
            sell_reason = strategy.tick(current_row['date'], day_offset, open_price, close_price, volume)
            if sell_reason is not None:
                backtest_result = strategy.get_backtest_result()
                buy_date = backtest_result["buy_date"]
                sell_date = backtest_result["sell_date"]
                buy_price = backtest_result["buy_price"]
                sell_price = backtest_result["sell_price"]
                hold_days = backtest_result["hold_days"]
                profit = backtest_result["profit"]
                profit_ratio = backtest_result["profit_ratio"]

                total_trades += 1
                if profit > 0:
                    winning_trades += 1
                total_profit += profit_ratio

                backtest_results.append({
                    "pattern": pattern["pattern"],
                    "chinese_name": pattern["chinese_name"],
                    "signal_date": pattern["date"],
                    "buy_date": buy_date.strftime('%Y-%m-%d') if buy_date else None,
                    "buy_price": round(buy_price, 2),
                    "sell_date": sell_date.strftime('%Y-%m-%d') if sell_date else None,
                    "sell_price": round(sell_price, 2),
                    "hold_days": hold_days,
                    "profit": round(profit, 2),
                    "profit_ratio": round(profit_ratio, 2),
                    "sell_reason": sell_reason
                 })
                break
    
    # 计算胜率
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    return {
        "backtest_results": backtest_results,
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "win_rate": round(win_rate, 2),
        "total_profit": round(total_profit, 2)
    }
