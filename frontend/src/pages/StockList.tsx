import { useEffect, useState } from 'react'
import { getCompanies } from '../api/companies'
import './StockList.css'

interface StockListProps {
  selectedStock: string
  onStockSelect: (securityCode: string) => void
}

export default function StockList({ selectedStock, onStockSelect }: StockListProps) {
  const [companies, setCompanies] = useState<any[]>([])
  const [isInitialized, setIsInitialized] = useState(false)

  // 获取所有股票列表
  useEffect(() => {
    ;(async () => {
      try {
        const res = await getCompanies()
        if (res?.data) {
          setCompanies(res.data)
        }
      } catch (error) {
        console.error('获取股票列表失败:', error)
      }
    })()
  }, [])

  // 初始加载时自动选择第一只股票
  useEffect(() => {
    if (companies.length > 0 && !isInitialized && !selectedStock) {
      const firstStock = companies[0]
      onStockSelect(firstStock.security_code)
      setIsInitialized(true)
    }
  }, [companies, isInitialized, onStockSelect, selectedStock])

  return (
    <aside className="stock-list">
      <h3 className="stock-list-title">股票列表</h3>
      <div className="stock-list-content">
        {companies.map((stock) => (
          <div
            key={stock.security_code}
            className={`stock-item ${selectedStock === stock.security_code ? 'active' : ''}`}
            onClick={() => onStockSelect(stock.security_code)}
          >
            <div className="stock-item-name">{stock.security_name_abbr}</div>
            <div className="stock-item-code">{stock.security_code}</div>
          </div>
        ))}
      </div>
    </aside>
  )
}