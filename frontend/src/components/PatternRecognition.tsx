import { useState, useEffect, useRef } from 'react'
import { SearchOutlined, BarChartOutlined } from '@ant-design/icons'
import { Select, DatePicker, InputNumber, Button, Table, Spin, Alert } from 'antd'
import { getCompanies } from '../api/companies'
import { getPatterns, getAllPatterns } from '../api/patterns'
import { getPinyin, getPinyinFirstLetters } from '../lib/utils'
import './PatternRecognition.css'

const { Option } = Select
const { RangePicker } = DatePicker

// 初始空形态列表，将从API获取
let AVAILABLE_PATTERNS = []

const getPatternDirection = (direction) => {
  return direction === 'bullish' ? '看涨' : '看跌'
}

const getDirectionColor = (direction) => {
  return direction === 'bullish' ? 'red' : 'green'
}

export default function PatternRecognition() {
  const [companies, setCompanies] = useState([])
  const [selectedStocks, setSelectedStocks] = useState([])
  const [loadingCompanies, setLoadingCompanies] = useState(false)

  const [selectedPatterns, setSelectedPatterns] = useState([])
  const [availablePatterns, setAvailablePatterns] = useState([])
  const [loadingPatterns, setLoadingPatterns] = useState(false)

  const [dateRange, setDateRange] = useState([])
  const [detectionDays, setDetectionDays] = useState(30)

  const [isDetecting, setIsDetecting] = useState(false)
  const [detectionResults, setDetectionResults] = useState([])
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [tableHeight, setTableHeight] = useState(400)
  const resultsRef = useRef(null)

  useEffect(() => {
    // 同时加载公司列表和形态列表
    Promise.all([loadCompanies(), loadPatterns()])
  }, [])

  useEffect(() => {
    // 动态计算表格高度
    const calculateTableHeight = () => {
      if (resultsRef.current) {
        const resultsContainer = resultsRef.current;
        const header = resultsContainer.querySelector('.pr-results-header');
        
        if (header) {
          const resultsHeight = resultsContainer.offsetHeight;
          const headerHeight = header.offsetHeight;
          const padding = 20; // 预留一些边距
          const calculatedHeight = resultsHeight - headerHeight - padding;
          
          if (calculatedHeight > 200) { // 最小高度限制
            setTableHeight(calculatedHeight);
          } else {
            setTableHeight(200); // 确保表格有最小高度
          }
        }
      }
    };

    // 初始计算
    calculateTableHeight();

    // 监听窗口大小变化
    window.addEventListener('resize', calculateTableHeight);

    // 监听检测结果变化
    if (detectionResults.length > 0) {
      setTimeout(calculateTableHeight, 100); // 延迟计算，确保DOM已更新
    }

    // 清理
    return () => {
      window.removeEventListener('resize', calculateTableHeight);
    };
  }, [detectionResults])

  const loadCompanies = async () => {
    setLoadingCompanies(true)
    try {
      const data = await getCompanies()
      if (data && data.data) {
        setCompanies(data.data)
      }
    } catch (err) {
      console.error('加载股票列表失败:', err)
    } finally {
      setLoadingCompanies(false)
    }
  }

  const loadPatterns = async () => {
    setLoadingPatterns(true)
    try {
      const data = await getAllPatterns()
      if (data && data.patterns) {
        setAvailablePatterns(data.patterns)
        // 更新全局AVAILABLE_PATTERNS变量
        AVAILABLE_PATTERNS = data.patterns
      }
    } catch (err) {
      console.error('加载形态列表失败:', err)
      // 如果API调用失败，使用默认的形态列表
      if (AVAILABLE_PATTERNS.length === 0) {
        // 这里可以添加一些默认形态，以防API调用失败
      }
    } finally {
      setLoadingPatterns(false)
    }
  }

  const handleDetect = async () => {
    if (!selectedStocks || selectedStocks.length === 0) {
      setError('请选择股票')
      return
    }

    setError(null)
    setIsDetecting(true)
    setDetectionResults([])
    setCurrentPage(1) // 重置分页到第一页

    try {
      const allResults = []
      
      // 遍历所有选中的股票
      for (const stockCode of selectedStocks) {
        const params = {
          days: detectionDays,
          start: dateRange.length > 0 ? dateRange[0] : '',
          end: dateRange.length > 0 ? dateRange[1] : ''
        }

        if (selectedPatterns.length > 0) {
          params.patterns = selectedPatterns
        }

        const results = await getPatterns(stockCode, params)
        if (results.patterns && results.patterns.length > 0) {
          // 为每个结果添加股票代码
          const stockResults = results.patterns.map(pattern => ({
            ...pattern,
            stock_code: stockCode
          }))
          allResults.push(...stockResults)
        }
      }
      
      setDetectionResults(allResults)
    } catch (err) {
      console.error('形态检测失败:', err)
      setError('形态检测失败，请稍后重试')
    } finally {
      setIsDetecting(false)
    }
  }

  const columns = [
    {
      title: '股票名称',
      dataIndex: 'stock_code',
      key: 'stock_name',
      render: (stockCode) => {
        const company = companies.find(c => c.security_code === stockCode)
        return company ? company.security_name_abbr : ''
      },
      width: 120
    },
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100
    },
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      width: 120
    },
    {
      title: '形态名称',
      dataIndex: 'chinese_name',
      key: 'chinese_name',
      ellipsis: true
    },
    {
      title: '方向',
      dataIndex: 'direction',
      key: 'direction',
      render: (direction) => {
        const text = getPatternDirection(direction)
        const color = getDirectionColor(direction)
        return <span style={{ color }}>{text}</span>
      },
      width: 80
    },
    {
      title: '信号强度',
      dataIndex: 'value',
      key: 'value',
      render: (value) => {
        return <span>{value > 0 ? '+' : ''}{value}</span>
      },
      width: 100
    }
  ]

  const getStockLabel = (value) => {
    const company = companies.find(c => c.security_code === value)
    return company ? `${company.security_code} ${company.security_name_abbr}` : value
  }

  const getPatternLabel = (value) => {
    const pattern = AVAILABLE_PATTERNS.find(p => p.name === value)
    return pattern ? pattern.chinese : value
  }

  return (
    <div className="pattern-recognition">
      <div className="pr-controls">
        <div className="pr-control-group">
          <label className="pr-label">选择股票</label>
          <Select
            mode="multiple"
            allowClear
            showSearch
            style={{ width: 300 }}
            placeholder="搜索并选择股票代码或名称"
            loading={loadingCompanies}
            optionFilterProp="children"
            onChange={setSelectedStocks}
            maxTagCount="responsive"
            tagRender={(props) => {
              const { value, closable, onClose } = props
              return (
                <span className="ant-select-tag">
                  {getStockLabel(value)}
                  {closable && (
                    <span
                      className="ant-select-tag-close"
                      onClick={(e) => {
                        e.stopPropagation()
                        onClose()
                      }}
                    >
                      ×
                    </span>
                  )}
                </span>
              )
            }}
            filterOption={(input, option) => {
              if (!option || !option.children) return false
              const childrenStr = typeof option.children === 'string' ? option.children : String(option.children)
              const lowerInput = input.toLowerCase()
              
              // 提取股票名称（假设格式为 "代码 名称"）
              const nameMatch = childrenStr.match(/\s+(.+)$/)
              const stockName = nameMatch ? nameMatch[1] : childrenStr
              
              // 检查是否匹配文本、拼音或拼音首字母
              return (
                childrenStr.toLowerCase().includes(lowerInput) ||
                getPinyin(stockName).includes(lowerInput) ||
                getPinyinFirstLetters(stockName).includes(lowerInput)
              )
            }}
          >
            {companies.map((company) => (
              <Option key={company.security_code} value={company.security_code}>
                {company.security_code} {company.security_name_abbr}
              </Option>
            ))}
          </Select>
        </div>

        <div className="pr-control-group">
          <label className="pr-label">选择形态</label>
          <Select
            mode="multiple"
            allowClear
            showSearch
            style={{ width: 200 }}
            placeholder="选择K线形态"
            loading={loadingPatterns}
            onChange={setSelectedPatterns}
            maxTagCount="responsive"
            tagRender={(props) => {
              const { value, closable, onClose } = props
              return (
                <span className="ant-select-tag">
                  {getPatternLabel(value)}
                  {closable && (
                    <span
                      className="ant-select-tag-close"
                      onClick={(e) => {
                        e.stopPropagation()
                        onClose()
                      }}
                    >
                      ×
                    </span>
                  )}
                </span>
              )
            }}
            filterOption={(input, option) => {
              if (!option || !option.children) return false
              const childrenStr = typeof option.children === 'string' ? option.children : String(option.children)
              const lowerInput = input.toLowerCase()
              
              // 检查是否匹配文本、拼音或拼音首字母
              return (
                childrenStr.toLowerCase().includes(lowerInput) ||
                getPinyin(childrenStr).includes(lowerInput) ||
                getPinyinFirstLetters(childrenStr).includes(lowerInput)
              )
            }}
          >
            {availablePatterns.map((pattern) => (
              <Option key={pattern.name} value={pattern.name}>
                {pattern.chinese}
              </Option>
            ))}
          </Select>
        </div>

        <div className="pr-control-group">
          <label className="pr-label">检测时间范围</label>
          <RangePicker
            style={{ width: 250 }}
            onChange={(dates) => {
              if (dates) {
                setDateRange([
                  dates[0].format('YYYY-MM-DD'),
                  dates[1].format('YYYY-MM-DD')
                ])
              } else {
                setDateRange([])
              }
            }}
          />
        </div>

        <div className="pr-control-group pr-days-group">
          <label className="pr-label">或近N天</label>
          <InputNumber
            min={1}
            max={365}
            value={detectionDays}
            onChange={setDetectionDays}
            style={{ width: 100 }}
          />
        </div>

        <Button
          type="primary"
          icon={<SearchOutlined />}
          loading={isDetecting}
          disabled={isDetecting || (!selectedStocks || selectedStocks.length === 0)}
          onClick={handleDetect}
        >
          开始检测
        </Button>
      </div>

      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          showIcon
          style={{ margin: '16px 0' }}
        />
      )}

      <div className="pr-results" ref={resultsRef}>
        <div className="pr-results-header">
          <h3>检测结果</h3>
          {selectedStocks && selectedStocks.length > 0 && (
            <span className="pr-results-info">
              已选 {selectedStocks.length} 只股票 · 最近 {detectionDays} 天
            </span>
          )}
        </div>

        {isDetecting ? (
          <div className="pr-loading">
            <Spin tip="检测中..." />
          </div>
        ) : detectionResults.length > 0 ? (
          <div className="pr-table-wrapper">
            <Table
              columns={columns}
              dataSource={detectionResults}
              rowKey={(record) => `${record.stock_code}-${record.date}-${record.pattern}`}
              pagination={{
                current: currentPage,
                pageSize: pageSize,
                showSizeChanger: true,
                pageSizeOptions: ['10', '20', '50', '100'],
                onChange: (page, size) => {
                  setCurrentPage(page);
                  setPageSize(size);
                  console.log('页码:', page, '每页条数:', size);
                }
              }}
              scroll={{ y: tableHeight }}
            />
          </div>
        ) : (
          <div className="pr-no-results">
            在指定时间范围内未检测到选定的K线形态
          </div>
        )}
      </div>
    </div>
  )
}
