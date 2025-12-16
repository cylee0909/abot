# 导出数据库连接实例
from .connection import db

# 导出模型初始化函数
from .models import init_tables

# 导出股票历史数据相关操作
from .stock_history import (
    init_table as init_stock_history_table,
    save_to_database as save_stock_history,
    get_stock_count,
    get_latest_date as get_latest_stock_date
)

from .companies import (
    init_table as init_companies_table,
    update_companies as update_companies,
    get_companies as get_companies,
    get_companies_with_details as get_companies_with_details
)