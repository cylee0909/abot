from .connection import db

def init_tables():
    """初始化所有数据库表"""
    from . import stock_history
    from . import hs300_components
    
    # 初始化stock_history表
    stock_history.init_table()
    
    # 初始化hs300_components表
    hs300_components.init_table()
