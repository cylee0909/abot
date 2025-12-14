#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import pandas as pd
import numpy as np
import logging
import re
from typing import Optional, List
import akshare as ak
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义StockInfo类
class StockInfo:
    def __init__(self, symbol: str, name: str, exchange: str, currency: str, 
                 price: float = 0.0, change: float = 0.0, changePercent: float = 0.0, 
                 marketCap: float = 0.0, volume: int = 0, pe: Optional[float] = None, 
                 dividend: Optional[float] = None):
        self.symbol = symbol
        self.name = name
        self.exchange = exchange
        self.currency = currency
        self.price = price
        self.change = change
        self.changePercent = changePercent
        self.marketCap = marketCap
        self.volume = volume
        self.pe = pe
        self.dividend = dividend
    
    def __repr__(self):
        return f"StockInfo(symbol='{self.symbol}', name='{self.name}', price={self.price}, change={self.changePercent}%)"

class StockDownloader:
    def __init__(self, max_concurrent: int = 20):
        """
        股票历史数据下载器初始化
        
        Args:
            max_concurrent: 最大并发请求数
        """
        self.max_concurrent = max_concurrent
        # AKShare初始化配置
        # 注意：新版本akshare可能不支持set_option方法，移除该配置
    
    async def _run_sync(self, func, *args, **kwargs):
        """
        在线程池中运行同步函数
        """
        return await asyncio.to_thread(func, *args, **kwargs)
    
    async def get_stock_historical_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取单只股票的历史数据
        实现主备用接口切换
        
        Args:
            stock_code: 股票代码 如 600519
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            股票历史数据DataFrame
        """
        import time
        import re

        market =  'SH'
        # 根据股票代码前缀确定正确的后缀
        if stock_code.startswith('30') or stock_code.startswith('00'):
            # 30开头是深交所创业板，00开头是深交所主板
            market = 'SZ'
        else:
            # 600开头是上交所主板，688开头是上交所科创板
            market = 'SH'
        
        full_symbol = f"{market.lower()}{stock_code}"

        for attempt in range(3):  # 重试3次
            try:
                logger.info(f"正在获取 {full_symbol} 历史数据 (尝试 {attempt+1}/3), 日期范围: {start_date} 至 {end_date}")
                
                # 尝试使用主接口获取数据
                df = None
                
                try:
                    logger.info(f"使用腾讯接口 stock_zh_a_hist_tx 获取 {full_symbol} 数据")
                    # 格式化日期，去除横杠
                    start_date_str = start_date.replace('-', '')
                    end_date_str = end_date.replace('-', '')
                    
                    df = await self._run_sync(
                        ak.stock_zh_a_hist_tx, 
                        symbol=full_symbol,
                        start_date=start_date_str,
                        end_date=end_date_str,
                        adjust="qfq"
                    )
                    logger.info(f"腾讯接口获取数据成功，数据行数: {len(df)}")
                    # 检查返回数据格式
                    if df is not None and not df.empty:
                        logger.info(f"腾讯接口返回列: {list(df.columns)}")
                except Exception as e:
                    logger.error(f"腾讯接口 stock_zh_a_hist_tx 获取 {full_symbol} 数据失败: {e}")
                
                
                if df is None or df.empty:
                    continue
                
                # 处理不同接口返回的数据格式差异
                logger.info(f"返回数据列: {list(df.columns)}")
                
                # 重命名列名，确保与原有代码兼容
                column_mapping = {}
                if '日期' in df.columns:
                    column_mapping['日期'] = 'date'
                elif 'date' in df.columns:
                    column_mapping['date'] = 'date'
                
                if '开盘' in df.columns:
                    column_mapping['开盘'] = 'open'
                    column_mapping['收盘'] = 'close'
                    column_mapping['最高'] = 'high'
                    column_mapping['最低'] = 'low'
                    column_mapping['成交量'] = 'amount'
                elif 'open' in df.columns:
                    column_mapping['open'] = 'open'
                    column_mapping['close'] = 'close'
                    column_mapping['high'] = 'high'
                    column_mapping['low'] = 'low'
                    column_mapping['amount'] = 'amount'
                
                df = df.rename(columns=column_mapping)
                
                # 检查必要列是否存在
                required_columns = ['date', 'open', 'close', 'high', 'low', 'amount']
                if not all(col in df.columns for col in required_columns):
                    logger.error(f"返回数据缺少必要列: {required_columns}")
                    logger.error(f"实际返回列: {list(df.columns)}")
                    continue
                
                # 只保留需要的列
                df = df[required_columns]
                
                # 添加股票代码列，确保df不为空
                if not df.empty:
                    df['stock_code'] = stock_code
                
                # 转换日期格式
                if not df.empty and isinstance(df['date'].iloc[0], str):
                    df['date'] = pd.to_datetime(df['date'])
                
                # 按日期排序，确保df不为空
                if not df.empty:
                    df = df.sort_values('date')
                
                logger.info(f"成功获取 {stock_code} 历史数据: {len(df)} 条记录")
                return df
                
            except Exception as e:
                logger.error(f"获取 {stock_code} 历史数据失败 (尝试 {attempt+1}/3): {e}")
                import traceback
                traceback.print_exc()
                
                # 重试前等待
                if attempt < 2:
                    wait_time = 2 * (2 ** attempt)
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"获取 {stock_code} 历史数据失败，已重试3次")
        return pd.DataFrame()
    
    async def search_stocks(self, query: str) -> List[StockInfo]:
        """
        搜索股票
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的股票信息列表
        """
        try:
            logger.info(f"正在搜索股票: {query}")
            # 获取A股股票列表
            stock_info_a_code_name_df = await self._run_sync(ak.stock_info_a_code_name)
            
            # 过滤匹配的股票
            filtered_stocks = stock_info_a_code_name_df[
                stock_info_a_code_name_df['code'].str.contains(query) | 
                stock_info_a_code_name_df['name'].str.contains(query)
            ]
            
            results = []
            for _, row in filtered_stocks.iterrows():
                # 判断交易所
                code = row['code']
                if code.startswith('6'):
                    exchange = "上海证券交易所"
                    symbol = f"{code}.SH"
                else:
                    exchange = "深圳证券交易所"
                    symbol = f"{code}.SZ"
                
                stock_info = StockInfo(
                    symbol=symbol,
                    name=row['name'],
                    exchange=exchange,
                    currency='CNY'
                )
                results.append(stock_info)
            
            return results[:10]  # 限制返回数量
        except Exception as e:
            logger.error(f"搜索股票时出错: {str(e)}")
            return []
    
    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """
        获取股票详细信息
        
        Args:
            symbol: 股票代码，格式如 600519.SH
            
        Returns:
            股票详细信息对象
        """
        try:
            logger.info(f"正在获取股票信息: {symbol}")
            # 解析股票代码
            code_match = re.match(r'(\d+)\.([A-Z]+)', symbol)
            if not code_match:
                return None
            
            code = code_match.group(1)
            market = code_match.group(2)
            
            # 获取实时行情，使用不需要token的API
            try:
                # 使用AKShare的实时行情API，不需要token
                df = await self._run_sync(ak.stock_zh_a_spot_em_)
                # 过滤出目标股票
                stock_df = df[df['代码'] == code]
                if stock_df.empty:
                    return None
                
                # 获取基本信息
                name = stock_df.iloc[0]['名称']
                exchange = "上海证券交易所" if market == "SH" else "深圳证券交易所"
                
                # 获取实时价格数据
                price = float(stock_df.iloc[0]['最新价']) if not pd.isna(stock_df.iloc[0]['最新价']) else 0.0
                change = float(stock_df.iloc[0]['涨跌额']) if not pd.isna(stock_df.iloc[0]['涨跌额']) else 0.0
                change_percent = float(stock_df.iloc[0]['涨跌幅']) if not pd.isna(stock_df.iloc[0]['涨跌幅']) else 0.0
                
                # 获取成交量（单位股，从万手转换为股）
                volume = int(stock_df.iloc[0]['成交量']) * 10000 if not pd.isna(stock_df.iloc[0]['成交量']) else 0
                
                # 初始化其他字段
                market_cap = 0.0
                pe = None
                dividend = None
                currency = 'CNY'
                
                # 尝试获取更多详细信息（如PE、市值等）
                try:
                    stock_info_df = await self._run_sync(ak.stock_individual_info_em, symbol=code)
                    if not stock_info_df.empty:
                        # 从股票信息中提取PE等数据
                        pe_data = stock_info_df[stock_info_df['item'] == '市盈率(TTM)']
                        if not pe_data.empty:
                            pe = float(pe_data.iloc[0]['value']) if not pd.isna(pe_data.iloc[0]['value']) else None
                            
                        # 提取市值数据
                        market_cap_data = stock_info_df[stock_info_df['item'].str.contains('总市值', na=False)]
                        if not market_cap_data.empty:
                            market_cap = float(market_cap_data.iloc[0]['value']) if not pd.isna(market_cap_data.iloc[0]['value']) else 0.0
                except Exception as e:
                    logger.warning(f"获取股票详细信息失败: {str(e)}")
                    # 继续执行，使用默认值
                
                stock_info = StockInfo(
                    symbol=symbol,
                    name=name,
                    exchange=exchange,
                    currency=currency,
                    price=price,
                    change=change,
                    changePercent=change_percent,
                    marketCap=market_cap,
                    volume=volume,
                    pe=pe,
                    dividend=dividend
                )
                return stock_info
            except Exception as e:
                logger.error(f"获取股票实时行情失败: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"获取股票信息时出错: {str(e)}")
            return None
    
    async def batch_get_stock_data(self, stock_codes: List[str], start_date: str, end_date: str) -> List[pd.DataFrame]:
        """
        批量获取股票历史数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            股票历史数据DataFrame列表
        """
        tasks = []
        
        for stock_code in stock_codes:
            task = self.get_stock_historical_data(stock_code, start_date, end_date)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"批量获取 {len(stock_codes)} 只股票的历史数据，成功获取 {len(results)} 条结果")
        # 过滤异常结果
        valid_results = []
        for stock_code, result in zip(stock_codes, results):
            if isinstance(result, Exception):
                logger.error(f"下载 {stock_code} 数据失败: {result}")
            elif not result.empty:
                valid_results.append(result)
        
        return valid_results

if __name__ == "__main__":
    # 测试下载器模块
    import asyncio
    
    async def test_downloader():
        downloader = StockDownloader()
        df = await downloader.get_stock_historical_data('600519.SH', '2025-01-01', '2025-12-13')
        print(f"获取到 {len(df)} 条贵州茅台历史数据")
        if not df.empty:
            print(df.head())
    
    asyncio.run(test_downloader())
