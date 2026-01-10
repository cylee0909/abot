import { useState, useEffect, useRef } from 'react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import StockDetail from './StockDetail'
import { PatternRecognition } from '../components'
import { getCompanies } from '../api/companies'

export default function MainLayout() {
  const [activeTab, setActiveTab] = useState('stock-detail')
  const [selectedStock, setSelectedStock] = useState('')
  const [companies, setCompanies] = useState([])
  const isInitialized = useRef(false)

  const handleStockSelect = (stockCode) => {
    setSelectedStock(stockCode)
    setActiveTab('stock-detail')
  }

  // 初始化时自动选择第一只股票
  useEffect(() => {
    if (isInitialized.current) return
    isInitialized.current = true

    const loadFirstStock = async () => {
      try {
        const res = await getCompanies()
        if (res?.data && res.data.length > 0) {
          setCompanies(res.data)
          const firstStock = res.data[0]
          setSelectedStock(firstStock.security_code)
        }
      } catch (error) {
        console.error('获取股票列表失败:', error)
      }
    }

    loadFirstStock()
  }, [])

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="stock-detail-container">
      <TabsList className="tab-list">
        <TabsTrigger value="stock-detail">股票详情</TabsTrigger>
        <TabsTrigger value="pattern">形态识别</TabsTrigger>
        <TabsTrigger value="backtest">策略回测</TabsTrigger>
      </TabsList>

      <TabsContent value="stock-detail">
        <StockDetail stockCode={selectedStock || undefined} activeTab={activeTab} companies={companies} />
      </TabsContent>

      <TabsContent value="pattern">
        <PatternRecognition onStockSelect={handleStockSelect} companies={companies} />
      </TabsContent>

      <TabsContent value="backtest">
        <div className="p-8 text-center text-gray-500">
          策略回测功能开发中...
        </div>
      </TabsContent>
    </Tabs>
  )
}
