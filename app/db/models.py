from .connection import db

def init_tables():
    """初始化所有数据库表"""
    from . import stock_history
    from . import components
    
    # 初始化stock_history表
    stock_history.init_table()
    
    # 初始化components表
    components.init_table()
