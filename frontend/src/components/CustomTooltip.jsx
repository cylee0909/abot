import { useEffect, useRef, useCallback } from 'react';

// 自定义tooltip样式
const tooltipStyle = `
  .echarts-tooltip-multiple {
    background: transparent;
    border: none;
    color: #333;
    padding: 0;
    border-radius: 0;
    position: fixed;
    pointer-events: none;
    z-index: 1000;
    font-size: 12px;
    box-shadow: none;
  }
`;

const CustomTooltip = ({ chart, data, maData, dif, dea, macd, MA_CONFIG }) => {
  const currentDataIndexRef = useRef(Math.max(0, data.dates.length - 1));
  const containerRef = useRef(null);

  // 获取图表容器的位置信息
  const getChartContainerRect = useCallback(() => {
    const container = containerRef.current;
    if (!container) return { left: 0, top: 0 };
    return container.getBoundingClientRect();
  }, []);
  
  // 创建并更新Tooltip
  const createOrUpdateTooltip = useCallback((id, content, left, top) => {
    let tooltip = document.getElementById(id);
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.id = id;
      tooltip.className = 'echarts-tooltip-multiple';
      tooltip.style.position = 'fixed'; // 使用fixed定位，相对于视口
      tooltip.style.pointerEvents = 'none';
      tooltip.style.zIndex = '1000';
      document.body.appendChild(tooltip);
    }
    tooltip.innerHTML = content;
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  }, []);
  
  // 清除Tooltip
  const clearTooltips = useCallback(() => {
    ['kline-tooltip', 'volume-tooltip', 'macd-tooltip'].forEach(id => {
      const tooltip = document.getElementById(id);
      if (tooltip) {
        document.body.removeChild(tooltip);
      }
    });
  }, []);
  
  // 数字格式化函数
  const formatNumber = useCallback((num) => {
    if (num >= 100000000) {
      return (num / 100000000).toFixed(2) + '亿';
    } else if (num >= 10000) {
      return (num / 10000).toFixed(2) + '万';
    } else {
      return num.toFixed(0);
    }
  }, []);

  // 更新Tooltip内容的函数
  const updateTooltips = useCallback((dataIndex) => {
    const rect = getChartContainerRect();
    
    // 只有当容器位置有效时才更新tooltip位置，避免闪烁
    if (rect.left === 0 && rect.top === 0) {
      // 容器位置无效，暂时隐藏tooltip
      clearTooltips();
      return;
    }
    
    // K线区域的Tooltip - 显示在图表容器内的左上角
    let klineHtml = '均线 ';
    const maLines = ['MA5', 'MA10', 'MA20', 'MA60'];
    maLines.forEach(maLine => {
      const maValue = maData[maLine][dataIndex];
      if (maValue && typeof maValue === 'number') {
        const color = MA_CONFIG.colors[maLine];
        klineHtml += `<span style="color: ${color};">${maLine}:${maValue.toFixed(2)} </span>`;
      }
    });
    createOrUpdateTooltip('kline-tooltip', klineHtml, rect.left + 50, rect.top + 10);
    
    // 成交量区域的Tooltip
    const volumeValue = data.volumes[dataIndex];
    createOrUpdateTooltip('volume-tooltip', `成交量: ${formatNumber(volumeValue)}`, rect.left + 50, rect.top + 270);
    
    // MACD区域的Tooltip
    const difValue = dif[dataIndex] || 0;
    const deaValue = dea[dataIndex] || 0;
    const macdValue = macd[dataIndex] || 0;
    createOrUpdateTooltip('macd-tooltip', `MACD: DIF:${difValue.toFixed(2)} DEA:${deaValue.toFixed(2)} MACD:${macdValue.toFixed(2)}`, rect.left + 50, rect.top + 370);
  }, [getChartContainerRect, createOrUpdateTooltip, maData, data.volumes, dif, dea, macd, MA_CONFIG, formatNumber]);

  useEffect(() => {
    if (!chart || !data.dates.length) return;

    // 设置容器引用
    containerRef.current = chart.getDom();

    // 初始显示最后一个数据
    currentDataIndexRef.current = Math.max(0, data.dates.length - 1);
    updateTooltips(currentDataIndexRef.current);
    
    // 使用chart.getZr()监听整个画布的鼠标移动事件，确保在任何位置都能触发
    const handleZrMousemove = (event) => {
      // 将鼠标像素坐标转换为图表坐标系中的数据坐标
      const pointInPixel = [event.offsetX, event.offsetY];
      
      // 转换为数据坐标，第一个参数是坐标系ID或索引，这里使用X轴索引0
      const pointInGrid = chart.convertFromPixel({ seriesIndex: 0, xAxisIndex: 0 }, pointInPixel);
      
      // 获取X轴数据索引
      if (pointInGrid && pointInGrid[0] !== undefined) {
        // 使用X轴数据索引
        let dataIndex = Math.round(pointInGrid[0]);
        
        // 确保索引在有效范围内
        dataIndex = Math.max(0, Math.min(data.dates.length - 1, dataIndex));
        
        // 更新tooltip
        if (dataIndex !== currentDataIndexRef.current) {
          currentDataIndexRef.current = dataIndex;
          updateTooltips(currentDataIndexRef.current);
        }
      }
    };

    // 监听axisPointer移动，确保tooltip跟随十字光标
    const handleAxisPointermove = (params) => {
      if (params.axisType === 'category' && params.axisIndex === 0) {
        // 使用axisPointer提供的valueIndex作为dataIndex
        const dataIndex = params.valueIndex !== undefined ? params.valueIndex : Math.round(params.value);
        if (dataIndex !== undefined && dataIndex >= 0 && dataIndex < data.dates.length) {
          currentDataIndexRef.current = dataIndex;
          updateTooltips(currentDataIndexRef.current);
        }
      }
    };

    function onResize() {
      chart.resize();
      updateTooltips(currentDataIndexRef.current); // 窗口大小变化时重新定位
    }

    // 绑定事件监听器
    const zr = chart.getZr();
    if (zr) {
      zr.on('mousemove', handleZrMousemove);
    }
    chart.on('axisPointermove', handleAxisPointermove);
    window.addEventListener('resize', onResize);

    // 添加样式标签
    const styleEl = document.createElement('style');
    styleEl.textContent = tooltipStyle;
    document.head.appendChild(styleEl);

    return () => {
      // 清理事件监听器
      const zr = chart.getZr();
      if (zr) {
        zr.off('mousemove', handleZrMousemove);
      }
      chart.off('axisPointermove', handleAxisPointermove);
      window.removeEventListener('resize', onResize);
      
      // 清除tooltip和样式
      clearTooltips();
      document.head.removeChild(styleEl);
    };
  }, [chart, data, maData, dif, dea, macd, MA_CONFIG, updateTooltips, clearTooltips]);

  return null;
};

export default CustomTooltip;