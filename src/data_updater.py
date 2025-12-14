#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sqlite3
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataUpdater:
    def __init__(self, db_path: str):
        """
        数据更新模块初始化
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
    
    def _init_database(self):
        """
        初始化数据库表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建沪深300成分股表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hs300_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secucode TEXT NOT NULL,
            security_code TEXT NOT NULL,
            type TEXT NOT NULL,
            security_name_abbr TEXT NOT NULL,
            close_price REAL NOT NULL,
            industry TEXT NOT NULL,
            region TEXT NOT NULL,
            weight REAL NOT NULL,
            eps REAL NOT NULL,
            bps REAL NOT NULL,
            roe REAL NOT NULL,
            total_shares REAL NOT NULL,
            free_shares REAL NOT NULL,
            free_cap REAL NOT NULL,
            f2 REAL NOT NULL,
            f3 REAL NOT NULL,
            update_date TEXT NOT NULL,
            UNIQUE(security_code)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def update_hs300_components(self, json_file_path: str):
        """
        将沪深300成分股JSON数据更新到数据库
        
        Args:
            json_file_path: JSON文件路径
        """
        if not os.path.exists(json_file_path):
            logger.error(f"沪深300成分股文件不存在: {json_file_path}")
            return False
        
        try:
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stocks = data['result']['data']
            update_date = datetime.now().strftime('%Y-%m-%d')
            
            # 初始化数据库表
            self._init_database()
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 插入或更新成分股数据
            for stock in stocks:
                cursor.execute('''
                REPLACE INTO hs300_components (
                    secucode, security_code, type, security_name_abbr, close_price, industry, 
                    region, weight, eps, bps, roe, total_shares, free_shares, free_cap, 
                    f2, f3, update_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    stock['SECUCODE'],
                    stock['SECURITY_CODE'],
                    stock['TYPE'],
                    stock['SECURITY_NAME_ABBR'],
                    stock['CLOSE_PRICE'],
                    stock['INDUSTRY'],
                    stock['REGION'],
                    stock['WEIGHT'],
                    stock['EPS'],
                    stock['BPS'],
                    stock['ROE'],
                    stock['TOTAL_SHARES'],
                    stock['FREE_SHARES'],
                    stock['FREE_CAP'],
                    stock['f2'],
                    stock['f3'],
                    update_date
                ))
            
            conn.commit()
            logger.info(f"成功保存 {len(stocks)} 只沪深300成分股到数据库")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"保存沪深300成分股失败: {e}")
            return False
    
    def get_hs300_stocks(self) -> list:
        """
        从数据库获取沪深300成分股列表
        
        Returns:
            股票代码列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT security_code FROM hs300_components')
            stocks = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            logger.info(f"成功读取 {len(stocks)} 只沪深300成分股")
            return stocks
        except Exception as e:
            logger.error(f"读取沪深300成分股失败: {e}")
            return []

if __name__ == "__main__":
    # 测试数据更新模块
    updater = DataUpdater('./data/hs300_history.db')
    updater.update_hs300_components('./data/hs300_components.json')
    stocks = updater.get_hs300_stocks()
    print(f"沪深300成分股数量: {len(stocks)}")
