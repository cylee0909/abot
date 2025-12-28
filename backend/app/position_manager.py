from typing import List, Dict, Optional
from datetime import datetime


class PositionManager:
    """
    仓位管理类，用于记录买入和卖出行为，计算盈亏比例和金额
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        初始化仓位管理器
        :param initial_capital: 初始资金，默认100000元
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = []  # 记录所有持仓记录
        self.trades = []  # 记录所有交易记录
        self.available_cash = initial_capital  # 可用现金
    
    def buy(self, symbol: str, price: float, quantity: int, date: Optional[str] = None) -> Dict[str, any]:
        """
        记录买入行为
        :param symbol: 股票代码
        :param price: 买入价格
        :param quantity: 买入数量
        :param date: 买入日期，格式为YYYY-MM-DD
        :return: 买入记录
        """
        # 计算买入金额
        amount = price * quantity
        
        # 检查资金是否足够
        if amount > self.available_cash:
            raise ValueError(f"资金不足，可用现金: {self.available_cash:.2f}，需要: {amount:.2f}")
        
        # 生成买入记录
        buy_record = {
            "id": len(self.trades) + 1,
            "symbol": symbol,
            "action": "buy",
            "price": price,
            "quantity": quantity,
            "amount": amount,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat()
        }
        
        # 更新交易记录
        self.trades.append(buy_record)
        
        # 更新可用现金
        self.available_cash -= amount
        
        # 更新持仓
        self._update_position(symbol, price, quantity, "buy")
        
        return buy_record
    
    def sell(self, symbol: str, price: float, quantity: int, date: Optional[str] = None) -> Dict[str, any]:
        """
        记录卖出行为
        :param symbol: 股票代码
        :param price: 卖出价格
        :param quantity: 卖出数量
        :param date: 卖出日期，格式为YYYY-MM-DD
        :return: 卖出记录，包含盈亏信息
        """
        # 检查持仓是否足够
        position = self.get_position(symbol)
        if not position or position["quantity"] < quantity:
            raise ValueError(f"持仓不足，当前持仓: {position['quantity'] if position else 0}，需要卖出: {quantity}")
        
        # 计算卖出金额
        amount = price * quantity
        
        # 计算盈亏
        avg_buy_price = position["avg_price"]
        profit = (price - avg_buy_price) * quantity
        profit_ratio = (price - avg_buy_price) / avg_buy_price * 100
        
        # 生成卖出记录
        sell_record = {
            "id": len(self.trades) + 1,
            "symbol": symbol,
            "action": "sell",
            "price": price,
            "quantity": quantity,
            "amount": amount,
            "profit": profit,
            "profit_ratio": profit_ratio,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat()
        }
        
        # 更新交易记录
        self.trades.append(sell_record)
        
        # 更新可用现金
        self.available_cash += amount
        
        # 更新持仓
        self._update_position(symbol, price, quantity, "sell")
        
        # 更新当前资金
        self.current_capital = self.available_cash + self.get_total_position_value()
        
        return sell_record
    
    def _update_position(self, symbol: str, price: float, quantity: int, action: str):
        """
        更新持仓信息
        :param symbol: 股票代码
        :param price: 成交价格
        :param quantity: 成交数量
        :param action: 操作类型，buy或sell
        """
        # 查找现有持仓
        position = next((p for p in self.positions if p["symbol"] == symbol), None)
        
        if action == "buy":
            if position:
                # 更新现有持仓
                total_cost = position["avg_price"] * position["quantity"] + price * quantity
                total_quantity = position["quantity"] + quantity
                position["avg_price"] = total_cost / total_quantity
                position["quantity"] = total_quantity
                position["current_price"] = price
            else:
                # 添加新持仓
                self.positions.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg_price": price,
                    "current_price": price
                })
        elif action == "sell":
            if position:
                # 减少持仓数量
                position["quantity"] -= quantity
                position["current_price"] = price
                
                # 如果持仓数量为0，移除该持仓
                if position["quantity"] <= 0:
                    self.positions.remove(position)
    
    def get_position(self, symbol: str) -> Optional[Dict[str, any]]:
        """
        获取指定股票的持仓信息
        :param symbol: 股票代码
        :return: 持仓信息，如果没有持仓则返回None
        """
        return next((p for p in self.positions if p["symbol"] == symbol), None)
    
    def get_all_positions(self) -> List[Dict[str, any]]:
        """
        获取所有持仓信息
        :return: 所有持仓列表
        """
        return self.positions.copy()
    
    def get_total_position_value(self) -> float:
        """
        计算总持仓市值
        :return: 总持仓市值
        """
        return sum(p["quantity"] * p["current_price"] for p in self.positions)
    
    def get_total_profit(self) -> float:
        """
        计算总盈亏金额
        :return: 总盈亏金额
        """
        return sum(trade.get("profit", 0) for trade in self.trades if trade["action"] == "sell")
    
    def get_total_profit_ratio(self) -> float:
        """
        计算总盈亏比例
        :return: 总盈亏比例（%）
        """
        if self.initial_capital == 0:
            return 0.0
        return (self.current_capital - self.initial_capital) / self.initial_capital * 100
    
    def get_trades(self, symbol: Optional[str] = None, action: Optional[str] = None) -> List[Dict[str, any]]:
        """
        获取交易记录
        :param symbol: 股票代码，可选，用于过滤特定股票的交易
        :param action: 操作类型，可选，buy或sell，用于过滤特定操作的交易
        :return: 交易记录列表
        """
        result = self.trades.copy()
        
        if symbol:
            result = [trade for trade in result if trade["symbol"] == symbol]
        
        if action:
            result = [trade for trade in result if trade["action"] == action]
        
        return result
    
    def get_summary(self) -> Dict[str, any]:
        """
        获取仓位管理汇总信息
        :return: 汇总信息
        """
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "available_cash": self.available_cash,
            "total_position_value": self.get_total_position_value(),
            "total_profit": self.get_total_profit(),
            "total_profit_ratio": self.get_total_profit_ratio(),
            "position_count": len(self.positions),
            "trade_count": len(self.trades),
            "buy_count": len([t for t in self.trades if t["action"] == "buy"]),
            "sell_count": len([t for t in self.trades if t["action"] == "sell"])
        }
    
    def update_current_price(self, symbol: str, price: float):
        """
        更新股票当前价格
        :param symbol: 股票代码
        :param price: 当前价格
        """
        position = self.get_position(symbol)
        if position:
            position["current_price"] = price
            # 更新总资金
            self.current_capital = self.available_cash + self.get_total_position_value()
    
    def reset(self, initial_capital: Optional[float] = None):
        """
        重置仓位管理器
        :param initial_capital: 重置后的初始资金，如果不提供则使用原初始资金
        """
        self.initial_capital = initial_capital or self.initial_capital
        self.current_capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.available_cash = self.initial_capital
