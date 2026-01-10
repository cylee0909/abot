import React, { useState } from "react"

function Tabs({ defaultValue, children, className }) {
  const [activeTab, setActiveTab] = useState(defaultValue)

  const tabsList = React.Children.toArray(children).find(
    child => child && child.type && child.type.displayName === 'TabsList'
  )
  
  const tabsContents = React.Children.toArray(children).filter(
    child => child && child.type && child.type.displayName === 'TabsContent'
  )

  return (
    <div className={className}>
      {tabsList && React.cloneElement(tabsList, { activeTab, setActiveTab })}
      {tabsContents.map(child => {
        if (activeTab === child.props.value) {
          return child
        }
        return null
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

function TabsContent({ children }) {
  return <div style={{ height: '100%', overflow: 'hidden' }}>{children}</div>
}
TabsContent.displayName = 'TabsContent'

export { Tabs, TabsList, TabsTrigger, TabsContent }
