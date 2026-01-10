import React, { useState, useRef, useEffect } from 'react'
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { getPinyin, getPinyinFirstLetters } from '../lib/utils'

interface SearchBarProps {
  placeholder?: string
  onSearch: (results: any[]) => void
  allItems: any[]
  onExpand?: (expanded: boolean) => void
}

export default function SearchBar({ 
  placeholder = "搜索", 
  onSearch, 
  allItems,
  onExpand
}: SearchBarProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // 搜索处理函数
  const handleSearch = (term: string) => {
    setSearchTerm(term)
    
    if (!term.trim()) {
      onSearch(allItems)
      return
    }

    const lowerTerm = term.toLowerCase()
    

    
    // 过滤项目
    const filtered = allItems.filter(item => {
      const itemNameLower = item.security_name_abbr.toLowerCase()
      const itemCodeLower = item.security_code.toLowerCase()
      const itemPinyin = getPinyin(item.security_name_abbr)
      const itemPinyinFirstLetters = getPinyinFirstLetters(item.security_name_abbr)
      
      return (
        itemNameLower.includes(lowerTerm) ||
        itemCodeLower.includes(lowerTerm) ||
        itemPinyin.includes(lowerTerm) ||
        itemPinyinFirstLetters.includes(lowerTerm)
      )
    })
    
    onSearch(filtered)
  }

  // 处理搜索框展开
  const handleExpand = () => {
    setIsExpanded(true)
    if (onExpand) {
      onExpand(true)
    }
  }

  // 处理搜索框收起
  const handleCollapse = () => {
    if (!searchTerm.trim()) {
      setIsExpanded(false)
      if (onExpand) {
        onExpand(false)
      }
    }
  }

  // 当搜索框展开时，自动聚焦输入框
  useEffect(() => {
    if (isExpanded && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [isExpanded])

  // 清空搜索框
  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSearchTerm('');
    // 直接调用 onSearch 传递当前的 allItems，确保返回当前分组的所有股票
    onSearch(allItems);
    setIsExpanded(false);
    if (onExpand) {
      onExpand(false);
    }
  }

  return (
    <div className="search-container">
      {isExpanded && (
        <input
          ref={searchInputRef}
          type="text"
          className="search-input"
          placeholder={placeholder}
          value={searchTerm}
          onChange={(e) => handleSearch(e.target.value)}
          onBlur={handleCollapse}
        />
      )}
      {searchTerm.trim() ? (
        <span 
          className={`search-icon clear-icon`}
          onClick={handleClear}
        >
          <XMarkIcon className="h-5 w-5" />
        </span>
      ) : (
        <span 
          className={`search-icon ${isExpanded ? 'expanded' : ''}`}
          onClick={handleExpand}
        >
          <MagnifyingGlassIcon className="h-5 w-5" />
        </span>
      )}
    </div>
  )
}
