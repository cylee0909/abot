import { useEffect, useState, useRef } from 'react'
import { getGroups, getGroupStocks, type Group } from '../api/groups'
import SearchBar from '../components/SearchBar'
import './StockList.css'

interface StockListProps {
  selectedStock: string
  onStockSelect: (securityCode: string) => void
  companies?: any[]
}

export default function StockList({ selectedStock, onStockSelect, companies: propCompanies }: StockListProps) {
  const [companies, setCompanies] = useState<any[]>([])
  const [allCompanies, setAllCompanies] = useState<any[]>([])
  const [currentGroupCompanies, setCurrentGroupCompanies] = useState<any[]>([])
  const [isInitialized, setIsInitialized] = useState(false)
  const [groups, setGroups] = useState<Group[]>([])
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null)
  const [showFilter, setShowFilter] = useState(false)
  const [loading, setLoading] = useState(false)
  const [isSearchExpanded, setIsSearchExpanded] = useState(false)
  const isGroupsLoaded = useRef(false)

  // 处理搜索结果
  const handleSearchResults = (results: any[]) => {
    setCompanies(results)
  }
  
  // 处理搜索框展开/收起
  const handleSearchExpand = (expanded: boolean) => {
    setIsSearchExpanded(expanded)
  }
  
  // 当分组变化时，重置搜索
  useEffect(() => {
    if (selectedGroupId !== null) {
      // 分组变化时，确保搜索框为空
      setIsSearchExpanded(false)
    }
  }, [selectedGroupId])

  // 当从父组件接收到股票列表时使用
  useEffect(() => {
    if (propCompanies && propCompanies.length > 0) {
      setCompanies(propCompanies)
      setAllCompanies(propCompanies)
      setCurrentGroupCompanies(propCompanies)
    }
  }, [propCompanies])

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
    if (!isGroupsLoaded.current) {
      fetchGroups()
      isGroupsLoaded.current = true
    }
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
        setCurrentGroupCompanies(allCompanies)
      } else {
        // 获取分组中的股票
        const groupStocks = await getGroupStocks(groupId, true)
        setCompanies(groupStocks)
        setCurrentGroupCompanies(groupStocks)
      }
    } catch (error) {
      console.error('筛选股票失败:', error)
      setCompanies(allCompanies)
      setCurrentGroupCompanies(allCompanies)
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
        <div className={`header-content ${isSearchExpanded ? 'search-expanded' : ''}`}>
          <h3 
            className="stock-list-title"
            onClick={() => setShowFilter(!showFilter)}
          >
            {selectedGroupId !== null ? getSelectedGroupName() : '全部'} ▼
          </h3>
          
          {/* 竖线分隔符 */}
          <div className="header-divider"></div>
          
          {/* 搜索框 */}
          <SearchBar
            placeholder="搜索股票名称、代码或拼音"
            onSearch={handleSearchResults}
            allItems={currentGroupCompanies}
            onExpand={handleSearchExpand}
          />
        </div>
        
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