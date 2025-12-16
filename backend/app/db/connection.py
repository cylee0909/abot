import sqlite3
import os
from .config import DB_CONFIG

class DatabaseConnection:
    """数据库连接管理类，实现单例模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._connection = None
        return cls._instance
    
    def connect(self):
        """建立数据库连接"""
        if self._connection is None:
            db_path = DB_CONFIG['database']
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self):
        """关闭数据库连接"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
    
    def get_cursor(self):
        """获取数据库游标"""
        return self.connect().cursor()
    
    def commit(self):
        """提交事务"""
        if self._connection is not None:
            self._connection.commit()
    
    def rollback(self):
        """回滚事务"""
        if self._connection is not None:
            self._connection.rollback()

# 创建全局数据库连接实例
db = DatabaseConnection()
