import sqlite3
import logging
import pandas as pd
from typing import Optional
from .connection import db

# 配置日志
logger = logging.getLogger(__name__)

def init_table():
    """初始化股票历史数据表"""
    cursor = db.get_cursor()
    
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
    
    db.commit()

def save_to_database(df: pd.DataFrame) -> bool:
    """将股票历史数据保存到SQLite数据库"""
    if df.empty:
        return False
    
    conn = db.connect()
    
    try:
        # 确保数据库表存在
        init_table()
        
        # 将DataFrame保存到数据库,使用append模式,利用UNIQUE约束处理重复数据
        df.to_sql('stock_history', conn, if_exists='append', index=False, 
                 dtype={'stock_code': 'TEXT', 'date': 'TEXT'})
        
        db.commit()
        logger.info(f"成功保存 {len(df)} 条数据到数据库")
        return True
    except Exception as e:
        logger.error(f"保存数据到数据库失败: {e}")
        db.rollback()
        return False

def get_stock_count() -> int:
    """获取数据库中股票历史数据的条数"""
    cursor = db.get_cursor()
    
    cursor.execute('SELECT COUNT(*) FROM stock_history')
    count = cursor.fetchone()[0]
    
    return count

def get_latest_date(stock_code: str) -> Optional[str]:
    """获取数据库中特定股票的最大日期"""
    cursor = db.get_cursor()
    
    cursor.execute('''
        SELECT MAX(date) FROM stock_history 
        WHERE stock_code = ?
    ''', (stock_code,))
    latest_date = cursor.fetchone()[0]
    
    return latest_date

def check_data_exists(stock_code: str, start_date: str, end_date: str) -> int:
    """检查数据库中特定股票在指定日期范围内的数据数量"""
    cursor = db.get_cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM stock_history 
        WHERE stock_code = ? AND date BETWEEN ? AND ?
    ''', (stock_code, start_date, end_date))
    count = cursor.fetchone()[0]
    
    return count
