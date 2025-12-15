#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
import logging

# 导入数据库模块
from app.db import update_companies, get_companies

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompaniesUpdater:
    def __init__(self, db_path: str):
        """
        数据更新模块初始化
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
    
    def update_companies(self, json_file_path: str):
        """
        将公司JSON数据更新到数据库
        
        Args:
            json_file_path: JSON文件路径
        """
        return update_companies(json_file_path)
    
    def get_companies(self) -> list:
        """
        从数据库获取公司列表
        
        Returns:
            股票代码列表
        """
        return get_companies()

if __name__ == "__main__":
    # 测试数据更新模块
    updater = CompaniesUpdater('./data/stock_history.db')
    updater.update_companies('./data/hs300_components.json')
    companies = updater.get_companies()
    print(f"公司数量: {len(companies)}")
