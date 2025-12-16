import { useEffect, useState } from 'react'
import { getCompanies } from '../api/companies'
import { getGroups, getGroupStocks, type Group } from '../api/groups'
import './StockList.css'

interface StockListProps {
  selectedStock: string
  onStockSelect: (securityCode: string) => void
}

export default function StockList({ selectedStock, onStockSelect }: StockListProps) {
  const [companies, setCompanies] = useState<any[]>([])
  const [allCompanies, setAllCompanies] = useState<any[]>([])
  const [isInitialized, setIsInitialized] = useState(false)
  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null)
  const [showFilter, setShowFilter] = useState(false)
  const [loading, setLoading] = useState(false)

  // 获取所有股票列表
  useEffect(() => {
    ;(async () => {
      try {
        const res = await getCompanies()
        if (res?.data) {
          setCompanies(res.data)
          setAllCompanies(res.data)
        }
      } catch (error) {
        console.error('获取股票列表失败:', error)
      }
    })()
  }, [])

  // 获取所有分组
  const fetchGroups = async () => {
    try {
      const data = await getGroups()
      setGroups(data)
    } catch (error) {
      console.error('获取分组列表失败:', error)
    }
  }

  // 初始化分组数据
  useEffect(() => {
    fetchGroups()
  }, [])

  // 当用户打开筛选下拉框时，刷新分组列表
  useEffect(() => {
    if (showFilter) {
      fetchGroups()
    }
  }, [showFilter])

  // 点击外部区域关闭筛选列表
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const header = document.querySelector('.stock-list-header');
      
      if (header && showFilter && !header.contains(target)) {
        setShowFilter(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showFilter])

  // 初始加载时自动选择第一只股票
  useEffect(() => {
    if (companies.length > 0 && !isInitialized && !selectedStock) {
      const firstStock = companies[0]
      onStockSelect(firstStock.security_code)
      setIsInitialized(true)
    }
  }, [companies, isInitialized, onStockSelect, selectedStock])

  // 根据分组筛选股票
  const filterByGroup = async (groupId: number | null) => {
    setLoading(true)
    setSelectedGroupId(groupId)
    setShowFilter(false)
    
    try {
      if (groupId === null) {
        // 显示所有股票
        setCompanies(allCompanies)
      } else {
        // 获取分组中的股票
        const groupStocks = await getGroupStocks(groupId, true)
        setCompanies(groupStocks)
      }
    } catch (error) {
      console.error('筛选股票失败:', error)
      setCompanies(allCompanies)
      setSelectedGroupId(null)
    } finally {
      setLoading(false)
    }
  }

  // 获取当前选中分组的名称
  const getSelectedGroupName = () => {
    if (selectedGroupId === null) return ''
    const group = groups.find(g => g.id === selectedGroupId)
    return group?.name || ''
  }

  return (
    <aside className="stock-list">
      {/* 股票列表标题和筛选功能 */}
      <div className="stock-list-header">
        <h3 
          className="stock-list-title"
          onClick={() => setShowFilter(!showFilter)}
        >
          股票列表
          {selectedGroupId !== null && (
            <span className="filter-tag">{getSelectedGroupName()}</span>
          )}
        </h3>
        
        {/* 分组筛选下拉框 */}
        {showFilter && (
          <div className="filter-dropdown">
            <div 
              className={`filter-item ${selectedGroupId === null ? 'active' : ''}`}
              onClick={() => filterByGroup(null)}
            >
              全部股票
            </div>
            {groups.map((group) => (
              <div 
                key={group.id} 
                className={`filter-item ${selectedGroupId === group.id ? 'active' : ''}`}
                onClick={() => filterByGroup(group.id)}
              >
                {group.name}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 股票列表内容 */}
      <div className="stock-list-content">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : companies.length === 0 ? (
          <div className="empty-list">
            {selectedGroupId === null ? '暂无股票数据' : '该分组下暂无股票'}
          </div>
        ) : (
          companies.map((stock) => (
            <div
              key={stock.security_code}
              className={`stock-item ${selectedStock === stock.security_code ? 'active' : ''}`}
              onClick={() => onStockSelect(stock.security_code)}
            >
              <div className="stock-item-name">{stock.security_name_abbr}</div>
              <div className="stock-item-code">{stock.security_code}</div>
            </div>
          ))
        )}
      </div>
    </aside>
  )
}