#!/bin/bash

# 指数成分股数据更新脚本
# 用途：定期从东方财富API获取沪深300和中证500成分股数据并保存到JSON文件

# 配置参数
DATA_DIR="./data"
LOG_FILE="${DATA_DIR}/update_log.txt"

# 沪深300配置
HS300_API_URL="https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=ROE&sortTypes=-1&pageSize=300&pageNumber=1&reportName=RPT_INDEX_TS_COMPONENT&columns=SECUCODE%2CSECURITY_CODE%2CTYPE%2CSECURITY_NAME_ABBR%2CCLOSE_PRICE%2CINDUSTRY%2CREGION%2CWEIGHT%2CEPS%2CBPS%2CROE%2CTOTAL_SHARES%2CFREE_SHARES%2CFREE_CAP&quoteColumns=f2%2Cf3&quoteType=0&source=WEB&client=WEB&filter=(TYPE%3D%221%22)"
HS300_OUTPUT_FILE="${DATA_DIR}/hs300_components.json"

# 中证500配置
CSI500_API_URL="https://datacenter-web.eastmoney.com/api/data/v1/get?sortColumns=ROE&sortTypes=-1&pageSize=500&pageNumber=1&reportName=RPT_INDEX_TS_COMPONENT&columns=SECUCODE%2CSECURITY_CODE%2CTYPE%2CSECURITY_NAME_ABBR%2CCLOSE_PRICE%2CINDUSTRY%2CREGION%2CWEIGHT%2CEPS%2CBPS%2CROE%2CTOTAL_SHARES%2CFREE_SHARES%2CFREE_CAP&quoteColumns=f2%2Cf3&quoteType=0&source=WEB&client=WEB&filter=(TYPE%3D%223%22)"
CSI500_OUTPUT_FILE="${DATA_DIR}/csi500_components.json"

# 确保数据目录存在
mkdir -p "${DATA_DIR}"

# 更新指数数据的函数
# 参数1：指数名称
# 参数2：API URL
# 参数3：输出文件路径
update_index_data() {
    local index_name="$1"
    local api_url="$2"
    local output_file="$3"
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始更新${index_name}成分股数据..." | tee -a "${LOG_FILE}"
    
    # 获取数据
    if curl -s -o "${output_file}" "${api_url}"; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ${index_name}数据更新成功！" | tee -a "${LOG_FILE}"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 文件保存路径：${output_file}" | tee -a "${LOG_FILE}"
        
        # 验证文件是否包含有效数据
        if grep -q "\"pages\"" "${output_file}"; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - ${index_name}数据格式验证通过" | tee -a "${LOG_FILE}"
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') - 警告：${index_name}数据格式可能存在问题" | tee -a "${LOG_FILE}"
        fi
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 错误：${index_name}数据更新失败！" | tee -a "${LOG_FILE}"
        return 1
    fi
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ${index_name}更新完成！" | tee -a "${LOG_FILE}"
    echo "----------------------------------------" | tee -a "${LOG_FILE}"
    return 0
}

# 执行更新
echo "$(date '+%Y-%m-%d %H:%M:%S') - ====== 开始指数成分股数据更新 ======" | tee -a "${LOG_FILE}"

update_index_data "沪深300" "${HS300_API_URL}" "${HS300_OUTPUT_FILE}"
hs300_result=$?

update_index_data "中证500" "${CSI500_API_URL}" "${CSI500_OUTPUT_FILE}"
csi500_result=$?

# 检查结果
if [ $hs300_result -eq 0 ] && [ $csi500_result -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ====== 所有指数数据更新成功 ======" | tee -a "${LOG_FILE}"
    exit 0
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ====== 部分指数数据更新失败 ======" | tee -a "${LOG_FILE}"
    exit 1
fi
