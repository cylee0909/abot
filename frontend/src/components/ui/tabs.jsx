import React, { useState, useEffect } from "react"

function Tabs({ defaultValue, value, onValueChange, children, className }) {
  const [activeTab, setActiveTab] = useState(value || defaultValue)

  // 当外部value变化时，更新内部状态
  useEffect(() => {
    if (value !== undefined) {
      setActiveTab(value)
    }
  }, [value])

  // 当内部状态变化时，调用外部回调
  const handleSetActiveTab = (newTab) => {
    setActiveTab(newTab)
    if (onValueChange) {
      onValueChange(newTab)
    }
  }

  const tabsList = React.Children.toArray(children).find(
    child => child && child.type && child.type.displayName === 'TabsList'
  )
  
  const tabsContents = React.Children.toArray(children).filter(
    child => child && child.type && child.type.displayName === 'TabsContent'
  )

  return (
    <div className={className}>
      {tabsList && React.cloneElement(tabsList, { activeTab, setActiveTab: handleSetActiveTab })}
      {tabsContents.map(child => {
        return React.cloneElement(child, {
          style: {
            ...child.props.style,
            display: activeTab === child.props.value ? 'block' : 'none',
            height: '100%',
            overflow: 'hidden'
          }
        })
      })}
    </div>
  )
}
Tabs.displayName = 'Tabs'

function TabsList({ children, activeTab, setActiveTab, className }) {
  return (
    <div className={className}>
      {React.Children.map(children, child => {
        if (!child) return null
        return React.cloneElement(child, { activeTab, onClick: () => setActiveTab(child.props.value) })
      })}
    </div>
  )
}
TabsList.displayName = 'TabsList'

function TabsTrigger({ value, children, activeTab, onClick, className }) {
  return (
    <button
      className={`${className || ''} ${activeTab === value ? 'active' : ''}`}
      onClick={onClick}
    >
      {children}
    </button>
  )
}
TabsTrigger.displayName = 'TabsTrigger'

function TabsContent({ children, style }) {
  return <div style={style}>{children}</div>
}
TabsContent.displayName = 'TabsContent'

export { Tabs, TabsList, TabsTrigger, TabsContent }
