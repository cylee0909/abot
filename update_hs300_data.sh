#!/bin/bash

# 沪深300成分股数据更新脚本
# 用途：定期从东方财富API获取沪深300成分股数据并保存到JSON文件

# 配置参数
API_URL="https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=ROE&sortTypes=-1&pageSize=300&pageNumber=1&reportName=RPT_INDEX_TS_COMPONENT&columns=SECUCODE%2CSECURITY_CODE%2CTYPE%2CSECURITY_NAME_ABBR%2CCLOSE_PRICE%2CINDUSTRY%2CREGION%2CWEIGHT%2CEPS%2CBPS%2CROE%2CTOTAL_SHARES%2CFREE_SHARES%2CFREE_CAP&quoteColumns=f2%2Cf3&quoteType=0&source=WEB&client=WEB&filter=(TYPE%3D%221%22)"
DATA_DIR="./data"
OUTPUT_FILE="${DATA_DIR}/hs300_components.json"
LOG_FILE="${DATA_DIR}/update_log.txt"

# 确保数据目录存在
mkdir -p "${DATA_DIR}"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始更新沪深300成分股数据..." | tee -a "${LOG_FILE}"

# 获取数据
if curl -s -o "${OUTPUT_FILE}" "${API_URL}"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 数据更新成功！" | tee -a "${LOG_FILE}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 文件保存路径：${OUTPUT_FILE}" | tee -a "${LOG_FILE}"
    
    # 验证文件是否包含有效数据
    if grep -q "\"pages\"" "${OUTPUT_FILE}"; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 数据格式验证通过" | tee -a "${LOG_FILE}"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 警告：数据格式可能存在问题" | tee -a "${LOG_FILE}"
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 错误：数据更新失败！" | tee -a "${LOG_FILE}"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 更新完成！" | tee -a "${LOG_FILE}"
echo "----------------------------------------" | tee -a "${LOG_FILE}"
