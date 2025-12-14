#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List
import pandas as pd

# 导入自定义模块
from src.data_updater import DataUpdater
from src.stock_downloader import StockDownloader

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self, db_path: str, max_concurrent: int = 50):
        """
        任务调度器初始化
        
        Args:
            db_path: 数据库文件路径
            max_concurrent: 最大并发请求数
        """
        self.db_path = db_path
        self.max_concurrent = max_concurrent
        self.updater = DataUpdater(db_path)
        self.downloader = StockDownloader(max_concurrent)
    
    def _init_stock_history_table(self):
        """
        初始化股票历史数据表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建股票历史数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            close REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock_code, date)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _save_to_database(self, df: pd.DataFrame):
        """
        将股票历史数据保存到SQLite数据库
        
        Args:
            df: 股票历史数据DataFrame
        """
        if df.empty:
            return False
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # 确保数据库表存在
            self._init_stock_history_table()
            
            # 将DataFrame保存到数据库,使用append模式,利用UNIQUE约束处理重复数据
            df.to_sql('stock_history', conn, if_exists='append', index=False, 
                     dtype={'stock_code': 'TEXT', 'date': 'TEXT'})
            
            conn.commit()
            logger.info(f"成功保存 {len(df)} 条数据到数据库")
            return True
        except Exception as e:
            logger.error(f"保存数据到数据库失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    async def run_download_task(self, start_date: str, end_date: str):
        """
        运行下载任务
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        """
        logger.info(f"开始运行下载任务")
        logger.info(f"时间范围: {start_date} 至 {end_date}")
        logger.info(f"最大并发数: {self.max_concurrent}")
        logger.info(f"数据库路径: {self.db_path}")
        
        # 1. 获取沪深300成分股列表
        stocks = self.updater.get_hs300_stocks()
        if not stocks:
            logger.error("没有获取到沪深300成分股列表，任务终止")
            return False
        
        logger.info(f"开始下载 {len(stocks)} 只股票的历史数据")
        
        # 2. 分批次下载数据
        batch_size = min(50, self.max_concurrent)
        success_count = 0
        skipped_count = 0
        
        for i in range(0, len(stocks), batch_size):
            batch = stocks[i:i+batch_size]
            logger.info(f"正在处理第 {i//batch_size + 1}/{(len(stocks) + batch_size - 1)//batch_size} 批次, {len(batch)} 只股票")
            
            # 检查批次中的每只股票是否需要下载
            stocks_to_download = []
            for stock in batch:
                stock_code = stock
                # 获取该股票的最大日期
                latest_date = self.get_latest_date_for_stock(stock_code)
                
                if latest_date is None:
                    # 没有历史数据，需要下载
                    stocks_to_download.append(stock)
                    logger.info(f"股票 {stock_code} 无历史数据，需要下载")
                elif latest_date < end_date:
                    # 历史数据的最大日期小于结束日期，需要下载更新
                    stocks_to_download.append(stock)
                    logger.info(f"股票 {stock_code} 历史数据最新日期为 {latest_date}，小于结束日期 {end_date}，需要下载更新")
                else:
                    # 历史数据已经是最新，跳过下载
                    logger.info(f"股票 {stock_code} 历史数据已更新到 {latest_date}，无需下载")
                    skipped_count += 1
            
            if not stocks_to_download:
                logger.info(f"本批次 {len(batch)} 只股票均已存在数据，跳过下载")
            else:
                logger.info(f"本批次需下载 {len(stocks_to_download)} 只股票，{len(batch) - len(stocks_to_download)} 只股票跳过")
                
                # 为每只需要下载的股票创建下载任务，使用正确的开始日期
                tasks = []
                for stock_code in stocks_to_download:
                    # 获取该股票的历史最大日期
                    latest_date = self.get_latest_date_for_stock(stock_code)
                    # 计算实际开始日期：如果有历史数据则从最大日期+1开始，否则使用原始start_date
                    actual_start_date = start_date
                    if latest_date is not None:
                        from datetime import datetime, timedelta
                        latest_date_obj = datetime.strptime(latest_date, '%Y-%m-%d')
                        next_date_obj = latest_date_obj + timedelta(days=1)
                        actual_start_date = next_date_obj.strftime('%Y-%m-%d')
                    # 创建下载任务
                    task = self.downloader.get_stock_historical_data(stock_code, actual_start_date, end_date)
                    tasks.append((stock_code, task))
                
                # 并发执行所有下载任务
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
                
                # 处理下载结果
                for (stock_code, _), result in zip(tasks, results):
                    if isinstance(result, Exception):
                        logger.error(f"下载 {stock_code} 数据失败: {result}")
                    elif not result.empty:
                        if self._save_to_database(result):
                            success_count += 1
                            logger.info(f"成功保存 {stock_code} 数据: {len(result)} 条记录")
                        else:
                            logger.error(f"保存 {stock_code} 数据失败")
                    else:
                        logger.info(f"{stock_code} 没有新增数据")
            
            # 批次间休息,避免请求过快
            if i + batch_size < len(stocks):
                await asyncio.sleep(1.0)
        
        logger.info(f"下载任务完成! 成功处理 {success_count} 只股票，跳过 {skipped_count} 只股票，总计 {success_count + skipped_count} 只股票")
        return True
    
    async def run_full_update(self, start_date: str, end_date: str, update_components: bool = True):
        """
        运行完整更新任务
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            update_components: 是否更新成分股列表
        """
        # 1. 更新成分股列表
        if update_components:
            logger.info("开始更新沪深300成分股列表")
            if not self.updater.update_hs300_components('./data/hs300_components.json'):
                logger.error("更新成分股列表失败")
                return False
        
        # 2. 下载历史数据
        logger.info("开始下载历史数据")
        return await self.run_download_task(start_date, end_date)
    
    def get_stock_count_in_db(self):
        """
        获取数据库中股票历史数据的条数
        
        Returns:
            股票历史数据条数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM stock_history')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_latest_date_for_stock(self, stock_code: str) -> str:
        """
        获取数据库中特定股票的最大日期
        
        Args:
            stock_code: 股票代码
        
        Returns:
            该股票的最大日期 (YYYY-MM-DD)，如果没有数据则返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(date) FROM stock_history 
            WHERE stock_code = ?
        ''', (stock_code,))
        latest_date = cursor.fetchone()[0]
        
        conn.close()
        return latest_date
    
    def check_stock_data_exists(self, stock_code: str, start_date: str, end_date: str) -> int:
        """
        检查数据库中特定股票在指定日期范围内的数据数量
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        Returns:
            数据库中该股票在指定日期范围内的数据条数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM stock_history 
            WHERE stock_code = ? AND date BETWEEN ? AND ?
        ''', (stock_code, start_date, end_date))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count

if __name__ == "__main__":
    # 测试任务调度器
    import asyncio
    
    async def test_scheduler():
        scheduler = TaskScheduler('./data/hs300_history.db')
        
        # 获取昨天的日期
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 运行完整更新
        await scheduler.run_full_update('2025-01-01', end_date, update_components=False)
        
        # 统计数据库中的数据条数
        count = scheduler.get_stock_count_in_db()
        print(f"数据库中历史数据条数: {count}")
    
    asyncio.run(test_scheduler())
