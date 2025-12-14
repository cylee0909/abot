# 沪深300成分股历史数据下载系统

## 项目介绍

本项目是一个用于下载和存储沪深300成分股历史数据的系统，支持从2015年至今的历史数据下载，并将数据存储到SQLite数据库中，方便后续分析和使用。

## 功能特点

- **异步下载**：使用异步编程提高下载效率，支持并发控制
- **模块化设计**：清晰的代码结构，便于维护和扩展
- **数据持久化**：将数据存储到SQLite数据库，便于后续查询和分析
- **自动更新**：支持定期更新成分股列表和历史数据
- **错误处理**：完善的错误处理机制，提高系统稳定性
- **重试机制**：网络请求失败时自动重试，提高下载成功率

## 技术栈

- **Python**：3.10+
- **异步框架**：asyncio + aiohttp
- **数据处理**：pandas + numpy
- **API库**：akshare（用于获取股票数据）
- **数据库**：SQLite
- **包管理器**：uv

## 项目结构

```
.
├── data/                 # 数据存储目录
│   ├── hs300_components.json  # 沪深300成分股JSON文件
│   ├── hs300_history.db        # SQLite数据库文件
│   └── update_log.txt          # 更新日志
├── app/                  # 源代码目录
│   ├── components_updater.py    # 数据更新模块
│   ├── stock_downloader.py     # 股票下载器模块
│   └── task_scheduler.py       # 任务调度模块
├── test/                 # 测试代码目录
│   ├── check_missing_stocks.py  # 检查缺失股票脚本
│   └── test_downloader.py       # 下载器测试脚本
├── main.py              # 主程序入口
├── pyproject.toml       # 项目配置文件
├── uv.lock              # uv依赖锁定文件
└── update_hs300_data.sh  # 数据更新脚本
```

## 安装步骤

1. **克隆项目**
   ```bash
   git clone <项目仓库地址>
   cd <项目目录>
   ```

2. **安装依赖**
   ```bash
   uv install
   ```

3. **获取沪深300成分股数据**
   ```bash
   bash update_hs300_data.sh
   ```

## 使用说明

### 1. 运行主程序

```bash
python main.py
```

主程序将自动完成以下工作：
- 更新沪深300成分股列表
- 下载所有成分股从2015-01-01至昨天的历史数据
- 将数据保存到SQLite数据库

### 2. 查看已下载的数据

```bash
# 查看数据库中的股票数量
sqlite3 data/hs300_history.db "SELECT COUNT(DISTINCT stock_code) FROM stock_history;"

# 查看总记录数
sqlite3 data/hs300_history.db "SELECT COUNT(*) FROM stock_history;"

# 查看单只股票的数据
sqlite3 data/hs300_history.db "SELECT * FROM stock_history WHERE stock_code='600519' LIMIT 10;"
```

### 3. 检查缺失的股票

```bash
python test/check_missing_stocks.py
```

### 4. 测试下载器

```bash
python test/test_downloader.py
```

## 模块说明

### 1. 数据更新模块 (`data_updater.py`)

- **功能**：负责将沪深300成分股JSON数据存储到数据库
- **主要方法**：
  - `update_hs300_components()`：将JSON数据更新到数据库
  - `get_hs300_stocks()`：从数据库获取沪深300成分股列表

### 2. 下载器模块 (`stock_downloader.py`)

- **功能**：支持下载某一只股票的指定周期历史数据
- **主要方法**：
  - `get_stock_historical_data()`：获取单只股票历史数据
  - `batch_get_stock_data()`：批量获取多只股票历史数据

### 3. 任务调度模块 (`task_scheduler.py`)

- **功能**：从数据库读取股票列表，调用下载器下载数据，并插入数据库
- **主要方法**：
  - `run_download_task()`：运行下载任务
  - `run_full_update()`：运行完整更新（成分股+历史数据）

## 配置说明

### 主程序配置

在`main.py`中可以修改以下配置：

- `db_path`：数据库文件路径
- `max_concurrent`：最大并发请求数
- `start_date`：开始日期
- `end_date`：结束日期

### 下载器配置

在`src/stock_downloader.py`中可以修改：

- 重试次数和超时设置

## 常见问题

### 1. 如何调整并发数？

修改`main.py`中的`max_concurrent`参数，建议根据网络情况调整，默认为20。

### 2. 如何更新成分股列表？

运行`bash update_hs300_data.sh`脚本，或修改`main.py`中的`update_components`参数为`True`，运行主程序。

## 依赖说明

| 依赖包 | 版本 | 用途 |
| --- | --- | --- |
| aiohttp | ^3.13.2 | 异步HTTP客户端 |
| pandas | ^2.3.3 | 数据处理和分析 |
| numpy | ^2.2.6 | 数值计算 |
| akshare | ^1.17.94 | 股票数据API |
| sqlite3 | 内置 | 数据库操作 |
| asyncio | 内置 | 异步编程 |

## 开发说明

### 运行测试

```bash
python -m pytest test/
```

### 添加新功能

1. 在对应模块中添加新功能
2. 编写测试用例
3. 运行测试确保功能正常
4. 更新README文档

## 贡献指南

欢迎提交Issue和Pull Request，贡献代码或提出改进建议。

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

如有问题或建议，欢迎联系项目维护者。

---

**更新时间**：2025-12-14
**版本**：1.0.0
