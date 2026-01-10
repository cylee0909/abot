#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
import logging
import requests
from typing import List

# 导入数据库模块
from db.companies import update_companies_from_data
from db.companies import get_companies

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
        
        # 指数配置
        self.index_configs = {
            "hs300": {
                "name": "沪深300",
                "url": "https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=ROE&sortTypes=-1&pageSize=300&pageNumber=1&reportName=RPT_INDEX_TS_COMPONENT&columns=SECUCODE%2CSECURITY_CODE%2CTYPE%2CSECURITY_NAME_ABBR%2CCLOSE_PRICE%2CINDUSTRY%2CREGION%2CWEIGHT%2CEPS%2CBPS%2CROE%2CTOTAL_SHARES%2CFREE_SHARES%2CFREE_CAP&quoteColumns=f2%2Cf3&quoteType=0&source=WEB&client=WEB&filter=(TYPE%3D%221%22)"
            },
            "csi500": {
                "name": "中证500",
                "url": "https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=ROE&sortTypes=-1&pageSize=500&pageNumber=1&reportName=RPT_INDEX_TS_COMPONENT&columns=SECUCODE%2CSECURITY_CODE%2CTYPE%2CSECURITY_NAME_ABBR%2CCLOSE_PRICE%2CINDUSTRY%2CREGION%2CWEIGHT%2CEPS%2CBPS%2CROE%2CTOTAL_SHARES%2CFREE_SHARES%2CFREE_CAP&quoteColumns=f2%2Cf3&quoteType=0&source=WEB&client=WEB&filter=(TYPE%3D%223%22)"
            }
        }
    
    def download_index_data(self, index_key: str):
        """
        从东方财富API下载指数成分股数据
        
        Args:
            index_key: 指数键值 (hs300 或 csi500)
        
        Returns:
            dict or None: 下载的数据，如果失败则返回None
        """
        if index_key not in self.index_configs:
            logger.error(f"无效的指数键值: {index_key}")
            return None
        
        config = self.index_configs[index_key]
        index_name = config["name"]
        url = config["url"]
        
        logger.info(f"开始更新{index_name}成分股数据...")
        
        try:
            # 获取数据
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 解析数据
            data = response.json()
            
            if "pages" in data:
                logger.info(f"{index_name}数据格式验证通过")
            else:
                logger.warning(f"警告：{index_name}数据格式可能存在问题")
            
            logger.info(f"{index_name}数据更新成功！")
            return data
        except Exception as e:
            logger.error(f"{index_name}数据更新失败: {e}")
            return None
    
    def download_all_index_data(self) -> dict:
        """
        下载所有指数成分股数据
        
        Returns:
            dict: 包含所有指数数据的字典，键为指数名称，值为数据
        """
        logger.info("====== 开始指数成分股数据更新 ======")
        
        results = {}
        for index_key in self.index_configs:
            data = self.download_index_data(index_key)
            if data:
                results[index_key] = data
        
        if len(results) == len(self.index_configs):
            logger.info("====== 所有指数数据更新成功 ======")
        else:
            logger.warning(f"====== 部分指数数据更新失败，成功更新 {len(results)} 个指数 ======")
        
        return results
    
    def update_companies(self):
        # 下载所有指数数据并更新
        index_data = self.download_all_index_data()
        
        if not index_data:
            logger.error("所有指数数据下载失败")
            return False
        
        # 更新每个指数的数据
        all_success = True
        for index_key, data in index_data.items():
            try:
                index_name = self.index_configs.get(index_key, {}).get('name', index_key)
                logger.info(f"开始更新{index_name}成分股到数据库...")
                
                # 验证数据结构
                if not data:
                    logger.error(f"{index_name}数据为空")
                    all_success = False
                    continue
                
                if 'result' not in data:
                    logger.error(f"{index_name}数据缺少result字段")
                    all_success = False
                    continue
                
                if 'data' not in data['result']:
                    logger.error(f"{index_name}数据缺少data字段")
                    all_success = False
                    continue
                
                stocks_data = data['result']['data']
                if not isinstance(stocks_data, list):
                    logger.error(f"{index_name}数据格式错误，data字段应为列表")
                    all_success = False
                    continue
                
                if not stocks_data:
                    logger.warning(f"{index_name}数据为空列表")
                    continue
                
                # 更新数据库
                success = update_companies_from_data(stocks_data)
                if success:
                    logger.info(f"{index_name}成分股更新到数据库成功，共{len(stocks_data)}只股票")
                else:
                    logger.error(f"{index_name}成分股更新到数据库失败")
                    all_success = False
            except Exception as e:
                logger.error(f"更新{index_name}成分股时发生错误: {e}")
                all_success = False
        
        return all_success

if __name__ == "__main__":
    # 测试数据更新模块
    updater = CompaniesUpdater('../data/stock_history.db')
    # 下载所有指数数据并更新数据库
    is_ok = updater.update_companies()
    print(f"update is ok ? {is_ok}")

    companies = get_companies()
    print(f"公司数量: {len(companies)}")