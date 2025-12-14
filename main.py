#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import argparse
from datetime import datetime, timedelta
from app.task_scheduler import TaskScheduler

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='ABot 股票数据更新工具')
    parser.add_argument('--db-path', type=str, default='./data/hs300_history.db', 
                        help='数据库路径 (默认: ./data/hs300_history.db)')
    parser.add_argument('--max-concurrent', type=int, default=50, 
                        help='最大并发数 (默认: 50)')
    parser.add_argument('--start-date', type=str, default='2015-01-01', 
                        help='开始日期 (默认: 2015-01-01)')
    parser.add_argument('--end-date', type=str, default=None, 
                        help='结束日期 (默认: 当前日期前2天)')
    parser.add_argument('--update-components', action='store_true', default=True, 
                        help='是否更新成分股列表 (默认: True)')
    parser.add_argument('--no-update-components', action='store_false', dest='update_components', 
                        help='不更新成分股列表')
    return parser.parse_args()

async def main(args):
    """
    程序主入口
    """
    # 配置参数
    db_path = args.db_path
    max_concurrent = args.max_concurrent
    start_date = args.start_date
    end_date = args.end_date if args.end_date else (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    update_components = args.update_components
    
    # 创建任务调度器
    scheduler = TaskScheduler(db_path, max_concurrent)
    
    # 运行完整更新任务
    await scheduler.run_full_update(start_date, end_date, update_components=update_components)
    
    # 统计数据库中的数据条数
    count = scheduler.get_stock_count_in_db()
    print(f"\n=== 任务完成 ===")
    print(f"数据库中历史数据总条数: {count}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"数据库路径: {db_path}")

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
