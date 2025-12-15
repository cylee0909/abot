# 公司历史数据下载系统

## 项目介绍

本项目是一个用于下载和存储公司历史数据的系统，支持从2015年至今的历史数据下载，并将数据存储到SQLite数据库中，方便后续分析和使用。

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
│   ├── hs300_components.json  # 公司JSON文件
│   ├── hs300_history.db        # SQLite数据库文件
│   └── update_log.txt          # 更新日志
├── app/                  # 源代码目录
│   ├── db/                  # 数据库相关模块
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── connection.py
│   │   ├── components.py
│   │   ├── models.py
│   │   └── stock_history.py
│   ├── components_updater.py    # 成分股更新模块
│   ├── stock_downloader.py     # 股票下载器模块
│   └── task_scheduler.py       # 任务调度模块
├── test/                 # 测试代码目录
│   ├── test_missing_stocks.py   # 检查缺失股票脚本
│   └── test_downloader.py       # 下载器测试脚本
├── analyze_data.py     # 数据分析脚本
├── main.py              # 主程序入口
├── pyproject.toml       # 项目配置文件
├── uv.lock              # uv依赖锁定文件
└── update_data.sh  # 数据更新脚本
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

3. **获取公司数据**
   ```bash
   bash update_data.sh
   ```

## 使用说明

### 1. 运行主程序

```bash
python main.py
```

主程序将自动完成以下工作：
- 更新公司列表
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
python test/test_missing_stocks.py
```

### 4. 测试下载器

```bash
python test/test_downloader.py
```

## 模块说明

### 1. 成分股更新模块 (`components_updater.py`)

- **功能**：负责将公司JSON数据存储到数据库，并提供成分股查询功能
- **主要方法**：
  - `update_components(json_file_path)`：将JSON数据更新到数据库
  - `get_components()`：从数据库获取公司列表

### 2. 股票下载器模块 (`stock_downloader.py`)

- **功能**：支持下载单只或多只股票的指定周期历史数据
- **主要方法**：
  - `get_stock_historical_data(stock_code, start_date, end_date)`：获取单只股票历史数据
  - `batch_get_stock_data(stock_codes, start_date, end_date)`：批量获取多只股票历史数据

### 3. 任务调度模块 (`task_scheduler.py`)

- **功能**：从数据库读取股票列表，调用下载器下载数据，并将数据插入数据库
- **主要方法**：
  - `run_download_task(start_date, end_date, stock_codes=None)`：运行下载任务
  - `run_update(start_date, end_date, update_components=True, stock_codes=None)`：运行完整更新（成分股+历史数据）
  - `get_stock_count_in_db()`：获取数据库中股票历史数据的条数

### 4. 数据库模块 (`app/db/`)

- **功能**：负责数据库连接、表结构定义和数据操作
- **主要文件**：
  - `config.py`：数据库配置
  - `connection.py`：数据库连接管理
  - `components.py`：公司数据操作
  - `stock_history.py`：股票历史数据操作
  - `models.py`：数据模型定义

## 配置说明

### 主程序配置

在`main.py`中可以修改以下配置：

- `db_path`：数据库文件路径
- `max_concurrent`：最大并发请求数
- `start_date`：开始日期
- `end_date`：结束日期

### 下载器配置

在`app/stock_downloader.py`中可以修改：

- 重试次数和超时设置

## 常见问题

### 1. 如何调整并发数？

修改`main.py`中的`max_concurrent`参数，建议根据网络情况调整，默认为50。

### 2. 如何更新成分股列表？

运行`bash update_data.sh`脚本，或在主程序中设置`update_components=True`运行。

### 3. 如何只下载指定股票的数据？

可以在调用`run_download_task`或`run_update`方法时，传入`stock_codes`参数指定要下载的股票代码列表。

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

**更新时间**：2025-12-15
**版本**：1.0.0
