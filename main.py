#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime, timedelta
from src.task_scheduler import TaskScheduler

async def main():
    """
    程序主入口
    """
    # 配置参数
    db_path = './data/hs300_history.db'
    max_concurrent = 50
    start_date = '2015-01-01'
    end_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    
    # 创建任务调度器
    scheduler = TaskScheduler(db_path, max_concurrent)
    
    # 运行完整更新任务
    # update_components=True 表示更新成分股列表
    await scheduler.run_full_update(start_date, end_date, update_components=True)
    
    # 统计数据库中的数据条数
    count = scheduler.get_stock_count_in_db()
    print(f"\n=== 任务完成 ===")
    print(f"数据库中历史数据总条数: {count}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"数据库路径: {db_path}")

if __name__ == "__main__":
    asyncio.run(main())
