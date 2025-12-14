#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
import logging

# 导入数据库模块
from app.db import update_hs300_components, get_hs300_components

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComponentsUpdater:
    def __init__(self, db_path: str):
        """
        数据更新模块初始化
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
    
    def update_hs300_components(self, json_file_path: str):
        """
        将沪深300成分股JSON数据更新到数据库
        
        Args:
            json_file_path: JSON文件路径
        """
        return update_hs300_components(json_file_path)
    
    def get_hs300_stocks(self) -> list:
        """
        从数据库获取沪深300成分股列表
        
        Returns:
            股票代码列表
        """
        return get_hs300_components()

if __name__ == "__main__":
    # 测试数据更新模块
    updater = ComponentsUpdater('./data/hs300_history.db')
    updater.update_hs300_components('./data/hs300_components.json')
    stocks = updater.get_hs300_stocks()
    print(f"沪深300成分股数量: {len(stocks)}")
