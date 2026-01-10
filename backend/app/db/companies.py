import json
import os
from datetime import datetime
import logging
from typing import List, Dict
from .connection import db

# 配置日志
logger = logging.getLogger(__name__)

def init_table():
    """初始化公司表"""
    cursor = db.get_cursor()
    
    # 创建公司表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS companies (
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

def update_companies_from_data(stocks: List[Dict]) -> bool:
    """将公司数据更新到数据库
    
    Args:
        stocks: 公司数据列表
    
    Returns:
        bool: 更新是否成功
    """
    try:
        update_date = datetime.now().strftime('%Y-%m-%d')
        
        # 初始化数据库表
        init_table()
        
        # 连接数据库
        cursor = db.get_cursor()
        
        # 插入或更新公司数据
        for stock in stocks:
            # 证券代码（带交易所前缀，如 sh600000）
            secucode = stock.get('SECUCODE') or ''
            # 股票代码（纯数字，如 600000）
            security_code = stock.get('SECURITY_CODE') or ''
            # 股票类型
            type_ = stock.get('TYPE') or ''
            # 股票简称
            name_abbr = stock.get('SECURITY_NAME_ABBR') or ''
            # 收盘价
            close_price = stock.get('CLOSE_PRICE') or 0.0
            # 所属行业
            industry = stock.get('INDUSTRY') or ''
            # 所属地区
            region = stock.get('REGION') or ''
            # 权重
            weight = stock.get('WEIGHT')
            weight = 0.0 if weight is None else weight
            # 每股收益
            eps = stock.get('EPS') or 0.0
            # 每股净资产
            bps = stock.get('BPS') or 0.0
            # 净资产收益率
            roe = stock.get('ROE') or 0.0
            # 总股本
            total_shares = stock.get('TOTAL_SHARES') or 0.0
            # 流通股本
            free_shares = stock.get('FREE_SHARES') or 0.0
            # 流通市值
            free_cap = stock.get('FREE_CAP') or 0.0
            # 涨幅（腾讯接口返回字段）
            f2 = stock.get('f2') or 0.0
            # 跌幅（腾讯接口返回字段）
            f3 = stock.get('f3') or 0.0

            cursor.execute('''
            REPLACE INTO companies (
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
        logger.info(f"成功保存 {len(stocks)} 只公司到数据库")
        return True
    except Exception as e:
        logger.error(f"保存公司失败: {e}")
        db.rollback()
        return False

def get_companies() -> List[str]:
    """从数据库获取公司列表"""
    try:
        cursor = db.get_cursor()
        
        cursor.execute('SELECT security_code FROM companies')
        stocks = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"成功读取 {len(stocks)} 只公司")
        return stocks
    except Exception as e:
        logger.error(f"读取公司失败: {e}")
        return []

def get_companies_with_details() -> List[Dict]:
    """从数据库获取公司详细信息"""
    try:
        cursor = db.get_cursor()
        
        cursor.execute('SELECT * FROM companies')
        rows = cursor.fetchall()
        
        # 将结果转换为字典列表
        stocks = []
        for row in rows:
            stock_dict = dict(row)
            stocks.append(stock_dict)
        
        logger.info(f"成功读取 {len(stocks)} 只公司详细信息")
        return stocks
    except Exception as e:
        logger.error(f"读取公司详细信息失败: {e}")
        return []

def get_company_by_code(security_code: str) -> Dict | None:
    try:
        cursor = db.get_cursor()
        cursor.execute('SELECT * FROM companies WHERE security_code = ?', (security_code,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"读取公司失败: {e}")
        return None
