#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import pandas as pd
import numpy as np
import logging
import re
import os
from typing import Optional, List, Tuple
import akshare as ak
from datetime import datetime
from app.config import settings

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
        # 解析股票代码
        market, stock_code = self._get_market_and_code(stock_code)
        
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
    
    def _get_market_and_code(self, stock_code: str) -> Tuple[str, str]:
        code_match = re.match(r'(\d+)\.([A-Z]+)', stock_code)
        if not code_match:
            market =  'SH'
            # 根据股票代码前缀确定正确的后缀
            if stock_code.startswith('30') or stock_code.startswith('00'):
                # 30开头是深交所创业板，00开头是深交所主板
                market = 'SZ'
            else:
                # 600开头是上交所主板，688开头是上交所科创板
                market = 'SH'
            return market, stock_code 
        
        code = code_match.group(1)
        market = code_match.group(2)
        return market, code


    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """获取股票详细信息"""
        try:
            market, code = self._get_market_and_code(symbol)
            
            # 获取实时行情
            try:
                df = await self._run_sync(ak.stock_individual_spot_xq,symbol=market+code,token=settings.XUEQIU_TOKEN)
            except Exception as e:
                print(f"获取xq股票信息失败: {str(e)}")
                import requests
                r = requests.get("https://xueqiu.com/hq", headers={"user-agent": "Mozilla"})
                t = r.cookies["xq_a_token"]
                settings.XUEQIU_TOKEN = t
                print(f"更新xq_a_token: {t}")
                df = await self._run_sync(ak.stock_individual_spot_xq,symbol=market+code,token=settings.XUEQIU_TOKEN)
            
            if df.empty:
                return None
                        
            # 获取股票名称
            name = df[df['item']=='名称'].iloc[0]['value']
            
            # 确定交易所
            exchange = "上海证券交易所" if market == "SH" else "深圳证券交易所"
            
            # 计算涨跌幅
            price = float(df[df['item']=='现价'].iloc[0]['value']) if not pd.isna(df[df['item']=='现价'].iloc[0]['value']) else 0.0
            change = float(df[df['item']=='涨跌'].iloc[0]['value']) if not pd.isna(df[df['item']=='涨跌'].iloc[0]['value']) else 0.0
            change_percent = float(df[df['item']=='涨幅'].iloc[0]['value']) if not pd.isna(df[df['item']=='涨幅'].iloc[0]['value']) else 0.0
            
            # 获取市值（亿元转为元）
            market_cap = float(df[df['item']=='资产净值/总市值'].iloc[0]['value']) if not pd.isna(df[df['item']=='资产净值/总市值'].iloc[0]['value']) else 0.0

            # 获取成交量（单位股）
            volume = int(float(df[df['item']=='成交量'].iloc[0]['value'])) if not pd.isna(df[df['item']=='成交量'].iloc[0]['value']) else 0

            # 获取市盈率
            pe = float(df[df['item']=='市盈率(TTM)'].iloc[0]['value']) if not pd.isna(df[df['item']=='市盈率(TTM)'].iloc[0]['value']) else None
            
            # 获取股息率
            dividend = float(df[df['item']=='股息率(TTM)'].iloc[0]['value']) if not pd.isna(df[df['item']=='股息率(TTM)'].iloc[0]['value']) else None

            # 获取货币
            currency = df[df['item']=='货币'].iloc[0]['value'] if not pd.isna(df[df['item']=='货币'].iloc[0]['value']) else 'CNY'
            
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
            print(f"获取股票信息时出错: {str(e)}")
            return None
    
    async def get_stock_chip_distribution(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取股票筹码分布数据
        
        Args:
            stock_code: 股票代码 如 600519 或 600519.SH
            
        Returns:
            筹码分布数据DataFrame，包含以下字段：
            - 日期 (date)
            - 获利比例 (profit_ratio)
            - 平均成本 (avg_cost)
            - 90%筹码集中度 (concentration_90)
            - 70%筹码集中度 (concentration_70)
        """
        try:
            logger.info(f"正在获取 {stock_code} 筹码分布数据")
            
            # 解析股票代码
            market, stock_code = self._get_market_and_code(stock_code)
            
            # 使用akshare的stock_cyq_em接口获取筹码分布数据
            df = await self._run_sync(
                ak.stock_cyq_em,
                symbol=stock_code
            )
            
            if df is None or df.empty:
                logger.error(f"未获取到 {stock_code} 筹码分布数据")
                return None
            
            logger.info(f"成功获取 {stock_code} 筹码分布数据，数据行数: {len(df)}")
            logger.info(f"筹码分布数据列: {list(df.columns)}")
            
            # 重命名列名，确保格式统一
            column_mapping = {
                '日期': 'date',
                '获利比例': 'profit_ratio',
                '平均成本': 'avg_cost',
                '90集中度': 'concentration_90',
                '70集中度': 'concentration_70'
            }
            
            # 只保留需要的列
            df = df.rename(columns=column_mapping)
            # 选择需要的列
            df = df[['date', 'profit_ratio', 'avg_cost', 'concentration_90', 'concentration_70']]
            
            # 转换日期格式
            if not df.empty and isinstance(df['date'].iloc[0], str):
                df['date'] = pd.to_datetime(df['date'])
            
            # 按日期排序
            if not df.empty:
                df = df.sort_values('date')
            
            return df
        except Exception as e:
            logger.error(f"获取 {stock_code} 筹码分布数据失败: {e}")
            import traceback
            traceback.print_exc()
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
        
        # 测试筹码分布接口
        chip_df = await downloader.get_stock_chip_distribution('600519.SH')
        print(f"\n获取到 {len(chip_df) if chip_df is not None else 0} 条贵州茅台筹码分布数据")
        if chip_df is not None and not chip_df.empty:
            print(chip_df.head())
            print(chip_df.tail())
    
    asyncio.run(test_downloader())
