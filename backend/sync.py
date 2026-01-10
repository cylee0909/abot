#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import argparse
from datetime import datetime, timedelta
from app.task_scheduler import TaskScheduler
from app.config import settings
from app.companies_updater import CompaniesUpdater

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='ABot 股票数据更新工具')
    parser.add_argument('--db-path', type=str, default=settings.DB_PATH, 
                        help='数据库路径 (默认: ./data/stock_history.db)')
    parser.add_argument('--max-concurrent', type=int, default=settings.MAX_CONCURRENT, 
                        help=f'最大并发数 (默认: {settings.MAX_CONCURRENT})')
    parser.add_argument('--start-date', type=str, default=settings.START_DATE, 
                        help=f'开始日期 (默认: {settings.START_DATE})')
    parser.add_argument('--end-date', type=str, default=(datetime.now()).strftime('%Y-%m-%d'), 
                        help='结束日期 (默认: 当前日期)')
    parser.add_argument('--update-companies', type=bool, default=settings.UPDATE_COMPANIES, 
                        help=f'是否更新公司列表 (默认: {settings.UPDATE_COMPANIES})')
    parser.add_argument('--stock-codes', type=str, nargs='*', default=None, 
                        help='指定的股票代码列表，多个股票代码用空格分隔 (默认: 所有公司)')
    return parser.parse_args()

async def main(args):
    """
    程序主入口
    """
    # 配置参数
    db_path = args.db_path
    max_concurrent = args.max_concurrent
    start_date = args.start_date
    end_date = args.end_date
    
    # 创建任务调度器
    scheduler = TaskScheduler(db_path, max_concurrent)
    
    # 运行完整更新任务
    if args.update_companies:
        CompaniesUpdater(db_path).update_companies()
    
    await scheduler.run_update(start_date, end_date, stock_codes=args.stock_codes)
    
    # 统计数据库中的数据条数
    count = scheduler.get_stock_count_in_db()
    print(f"\n=== 任务完成 ===")
    print(f"数据库中历史数据总条数: {count}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"数据库路径: {db_path}")

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
