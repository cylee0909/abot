import logging
import sqlite3
from typing import List, Dict, Optional
from .connection import db

# 配置日志
logger = logging.getLogger(__name__)

def init_table():
    """初始化股票分组相关表"""
    cursor = db.get_cursor()
    
    # 创建股票分组表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建股票分组关联表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        stock_code TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES stock_groups(id) ON DELETE CASCADE,
        UNIQUE(group_id, stock_code)
    )
    ''')
    
    db.commit()

# 分组相关操作
def create_group(name: str) -> int:
    """创建新分组"""
    try:
        cursor = db.get_cursor()
        cursor.execute(
            'INSERT INTO stock_groups (name) VALUES (?)',
            (name,)
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            logger.error(f"分组名称已存在: {name}")
        else:
            logger.error(f"创建分组失败: {e}")
        db.rollback()
        return -1
    except Exception as e:
        logger.error(f"创建分组失败: {e}")
        db.rollback()
        return -1

def delete_group(group_id: int) -> bool:
    """删除分组"""
    try:
        cursor = db.get_cursor()
        cursor.execute(
            'DELETE FROM stock_groups WHERE id = ?',
            (group_id,)
        )
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"删除分组失败: {e}")
        db.rollback()
        return False

def get_all_groups() -> List[Dict]:
    """获取所有分组"""
    try:
        cursor = db.get_cursor()
        cursor.execute('SELECT * FROM stock_groups ORDER BY id ASC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"获取分组列表失败: {e}")
        return []

def get_group_by_id(group_id: int) -> Optional[Dict]:
    """根据ID获取分组"""
    try:
        cursor = db.get_cursor()
        cursor.execute('SELECT * FROM stock_groups WHERE id = ?', (group_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"获取分组失败: {e}")
        return None

# 股票分组关联相关操作
def add_stock_to_group(group_id: int, stock_code: str) -> bool:
    """将股票添加到分组"""
    try:
        cursor = db.get_cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO stock_group_members (group_id, stock_code) VALUES (?, ?)',
            (group_id, stock_code)
        )
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"添加股票到分组失败: {e}")
        db.rollback()
        return False

def remove_stock_from_group(group_id: int, stock_code: str) -> bool:
    """从分组中移除股票"""
    try:
        cursor = db.get_cursor()
        cursor.execute(
            'DELETE FROM stock_group_members WHERE group_id = ? AND stock_code = ?',
            (group_id, stock_code)
        )
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"从分组中移除股票失败: {e}")
        db.rollback()
        return False

def get_stocks_in_group(group_id: int) -> List[str]:
    """获取分组中的所有股票"""
    try:
        cursor = db.get_cursor()
        cursor.execute(
            'SELECT stock_code FROM stock_group_members WHERE group_id = ?',
            (group_id,)
        )
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"获取分组股票列表失败: {e}")
        return []

def get_stocks_in_group_with_details(group_id: int) -> List[Dict]:
    """获取分组中的所有股票及详细信息"""
    try:
        cursor = db.get_cursor()
        cursor.execute('''
            SELECT c.* FROM companies c
            JOIN stock_group_members sgm ON c.security_code = sgm.stock_code
            WHERE sgm.group_id = ?
        ''', (group_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"获取分组股票详细信息失败: {e}")
        return []

def get_groups_for_stock(stock_code: str) -> List[Dict]:
    """获取股票所属的所有分组"""
    try:
        cursor = db.get_cursor()
        cursor.execute('''
            SELECT sg.* FROM stock_groups sg
            JOIN stock_group_members sgm ON sg.id = sgm.group_id
            WHERE sgm.stock_code = ?
        ''', (stock_code,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"获取股票所属分组失败: {e}")
        return []