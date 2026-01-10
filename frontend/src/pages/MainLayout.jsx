import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import StockDetail from './StockDetail'
import { PatternRecognition } from '../components'

export default function MainLayout() {
  return (
    <Tabs defaultValue="stock-detail" className="stock-detail-container">
      <TabsList className="tab-list">
        <TabsTrigger value="stock-detail">股票详情</TabsTrigger>
        <TabsTrigger value="pattern">形态识别</TabsTrigger>
        <TabsTrigger value="backtest">策略回测</TabsTrigger>
      </TabsList>

      <TabsContent value="stock-detail">
        <StockDetail />
      </TabsContent>

      <TabsContent value="pattern">
        <PatternRecognition />
      </TabsContent>

      <TabsContent value="backtest">
        <div className="p-8 text-center text-gray-500">
          策略回测功能开发中...
        </div>
      </TabsContent>
    </Tabs>
  )
}
