import json
import os
from datetime import datetime
import logging
from typing import List, Dict
from .connection import db

# 配置日志
logger = logging.getLogger(__name__)

def init_table():
    """初始化沪深300成分股表"""
    cursor = db.get_cursor()
    
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
    
    db.commit()

def update_components(json_file_path: str) -> bool:
    """将沪深300成分股JSON数据更新到数据库"""
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
        init_table()
        
        # 连接数据库
        cursor = db.get_cursor()
        
        # 插入或更新成分股数据
        for stock in stocks:
            secucode = stock.get('SECUCODE') or ''
            security_code = stock.get('SECURITY_CODE') or ''
            type_ = stock.get('TYPE') or ''
            name_abbr = stock.get('SECURITY_NAME_ABBR') or ''
            close_price = stock.get('CLOSE_PRICE') or 0.0
            industry = stock.get('INDUSTRY') or ''
            region = stock.get('REGION') or ''
            weight = stock.get('WEIGHT')
            weight = 0.0 if weight is None else weight
            eps = stock.get('EPS') or 0.0
            bps = stock.get('BPS') or 0.0
            roe = stock.get('ROE') or 0.0
            total_shares = stock.get('TOTAL_SHARES') or 0.0
            free_shares = stock.get('FREE_SHARES') or 0.0
            free_cap = stock.get('FREE_CAP') or 0.0
            f2 = stock.get('f2') or 0.0
            f3 = stock.get('f3') or 0.0

            cursor.execute('''
            REPLACE INTO hs300_components (
                secucode, security_code, type, security_name_abbr, close_price, industry,
                region, weight, eps, bps, roe, total_shares, free_shares, free_cap,
                f2, f3, update_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                secucode,
                security_code,
                type_,
                name_abbr,
                close_price,
                industry,
                region,
                weight,
                eps,
                bps,
                roe,
                total_shares,
                free_shares,
                free_cap,
                f2,
                f3,
                update_date
            ))
        
        db.commit()
        logger.info(f"成功保存 {len(stocks)} 只沪深300成分股到数据库")
        return True
    except Exception as e:
        logger.error(f"保存沪深300成分股失败: {e}")
        db.rollback()
        return False

def get_components() -> List[str]:
    """从数据库获取沪深300成分股列表"""
    try:
        cursor = db.get_cursor()
        
        cursor.execute('SELECT security_code FROM hs300_components')
        stocks = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"成功读取 {len(stocks)} 只沪深300成分股")
        return stocks
    except Exception as e:
        logger.error(f"读取沪深300成分股失败: {e}")
        return []

def get_components_with_details() -> List[Dict]:
    """从数据库获取沪深300成分股详细信息"""
    try:
        cursor = db.get_cursor()
        
        cursor.execute('SELECT * FROM hs300_components')
        rows = cursor.fetchall()
        
        # 将结果转换为字典列表
        stocks = []
        for row in rows:
            stock_dict = dict(row)
            stocks.append(stock_dict)
        
        logger.info(f"成功读取 {len(stocks)} 只沪深300成分股详细信息")
        return stocks
    except Exception as e:
        logger.error(f"读取沪深300成分股详细信息失败: {e}")
        return []
