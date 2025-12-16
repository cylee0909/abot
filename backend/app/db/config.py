import os

# 数据库配置
DB_CONFIG = {
    'database': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'stock_history.db')
}
