import os

# 数据库配置
DB_CONFIG = {
    'database': os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'hs300_history.db')
}
