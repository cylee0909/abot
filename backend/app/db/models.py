from .connection import db

def init_tables():
    """初始化所有数据库表"""
    from . import stock_history
    from . import companies
    from . import stock_groups
    
    # 初始化stock_history表
    stock_history.init_table()
    
    # 初始化companies表
    companies.init_table()
    
    # 初始化stock_groups相关表
    stock_groups.init_table()
