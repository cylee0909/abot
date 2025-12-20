import talib
import numpy as np
import pandas as pd

class PatternDetector:
    def __init__(self, open_p, high_p, low_p, close_p, volume, limit_threshold=0.098):
        self.o = pd.Series(open_p)
        self.h = pd.Series(high_p)
        self.l = pd.Series(low_p)
        self.c = pd.Series(close_p)
        self.v = pd.Series(volume)
        # 填充 NaN 避免计算中断
        self.o.ffill(inplace=True)
        self.h.ffill(inplace=True)
        self.l.ffill(inplace=True)
        self.c.ffill(inplace=True)
        self.v.fillna(0, inplace=True)
        
        self.n = len(self.c)
        self.limit_threshold = limit_threshold
        self._precalculate_indicators()

    def _precalculate_indicators(self):
        # === 基础均线 ===
        values = self.c.values
        self.ma5 = talib.SMA(values, 5)
        self.ma10 = talib.SMA(values, 10)
        self.ma30 = talib.SMA(values, 30)
        self.ma20 = talib.SMA(values, 20)
        self.ma60 = talib.SMA(values, 60)
        
        self.vma5 = talib.SMA(self.v.values, 5)
        self.vma10 = talib.SMA(self.v.values, 10)
        self.vma20 = talib.SMA(self.v.values, 20)

        # === 波动率 (关键优化) ===
        # 使用 ATR(14) 来定义"大幅波动"、"接近"等概念，而非固定百分比
        self.atr = talib.ATR(self.h.values, self.l.values, self.c.values, timeperiod=14)
        # 归一化 ATR，用于判断相对波幅
        self.natr = self.atr / self.c 
        
        # === MACD ===
        self.diff, self.dea, self.macd_hist = talib.MACD(values, fastperiod=12, slowperiod=26, signalperiod=9)
        
        # === Shift 数据 ===
        self.close_prev = self.c.shift(1)
        self.open_prev = self.o.shift(1)
        self.vol_prev = self.v.shift(1)
        self.high_prev = self.h.shift(1)
        self.low_prev = self.l.shift(1)

        # === 辅助逻辑 ===
        self.is_yang = self.c > self.o
        # 实体大小 (绝对值)
        self.body_abs = np.abs(self.c - self.o)
          # 高低位判断 (优化版)
        self.low_pos = self._check_position(is_low=True)
        self.high_pos = self._check_position(is_low=False)

    def _check_position(self, is_low=True, window=60):
        """向量化的高低位判断"""
        rolling_min = self.c.rolling(window).min()
        rolling_max = self.c.rolling(window).max()
        range_val = rolling_max - rolling_min
        # 防止除零
        range_val = range_val.replace(0, np.inf) 
        
        if is_low:
            # 当前价格 <= 最低价 + 振幅*0.3
            return self.c <= (rolling_min + range_val * 0.3)
        else:
            # 当前价格 >= 最高价 - 振幅*0.3
            return self.c >= (rolling_max - range_val * 0.3)

    # ================= 辅助工具 =================
    def _cross_over(self, a, b):
        """a 上穿 b (金叉)"""
        # (今天 a > b) AND (昨天 a <= b)
        prev_a = pd.Series(a).shift(1)
        prev_b = pd.Series(b).shift(1)
        return (a > b) & (prev_a <= prev_b)
    
    def _cross_under(self, a, b):
        """a 下穿 b (死叉)"""
        prev_a = pd.Series(a).shift(1)
        prev_b = pd.Series(b).shift(1)
        return (a < b) & (prev_a >= prev_b)

    # ================= 形态检测函数 (全向量化) =================

    def DOUBLE_BOTTOM(self):
        """
        双重底 (无未来函数版)
        逻辑：
        1. 左底 (LB): 20-60天前的最低点
        2. 右底 (RB): 5-20天前的最低点
        3. 颈线 (Neck): 两底之间的最高点
        4. 触发: 今天收盘突破颈线
        """
        # 定义窗口
        window_long = 60
        window_short = 20
        
        # 寻找过去60天的最低点 (排除最近5天，避免直接取到现在的低点)
        period_low = self.l.shift(5).rolling(window_long).min()
        
        # 寻找右底区域 (最近20天内的低点)
        recent_low = self.l.rolling(window_short).min()
        
        # 条件1: 两个低点要在同一个水平位 (差距不超过 1.5倍 ATR)
        # 这里用 ATR 替代固定的 3%
        bottoms_level = np.abs(recent_low - period_low) < (self.atr * 1.5)
        
        # 条件2: 颈线确认
        # 实际上很难精确找到两个具体低点中间的时间段。
        # 简化做法：过去 window_long 天的最高价(颈线)被突破? 不太对，那是突破大箱体。
        # 修正做法：取过去 window_long 天内，除去最近 window_short 天及其左侧对应低点后的区间最大值。
        # 向量化简化版：Breakout 20日新高，且之前有长期低点支撑
        
        # 1. 之前处于低位 (60天低点存在)
        is_low_position = self.l <= (period_low + self.atr)
        
        # 2. 经历了一波反弹和回调 (W型的中间高点存在)
        # 过去60天最高价 > 最低价 + 5*ATR (确保有波峰)
        has_peak = self.h.rolling(window_long).max() > (period_low + 5 * self.atr)
        
        # 3. 今天突破过去20天的高点 (右侧突破)
        breakout = (self.c > self.h.shift(1).rolling(20).max()) & (self.c > self.o)
        
        # 4. 确保不是单边上涨，而是有底部震荡 (最近的低点离当前Close有一定距离，但离PeriodLow很近)
        
        return (bottoms_level & has_peak & breakout).fillna(0).astype(int).values

    def DRAGONFLY_TOUCH_WATER(self):
        """
        蜻蜓点水 (动态阈值版)
        1. 趋势: MA20 向上
        2. 回踩: 最低价触碰 MA20 (距离小于 0.5 * ATR)
        3. 支撑: 收盘价在 MA20 上方，且不仅是触碰，还要有支撑反应 (如下影线)
        """
        # 1. 趋势向上 (MA20 比 5天前高)
        ma20_series = pd.Series(self.ma20)
        trend_up = self.ma20 > ma20_series.shift(5)
        
        # 2. 触碰逻辑: Low <= MA20 + 0.5*ATR (进入射程)
        # 且 Low >= MA20 - 0.5*ATR (没有发生有效击穿，或者击穿幅度很小)
        # 或者: Low 击穿了，但 Close 收回来了
        touch = (self.l <= (self.ma20 + 0.3 * self.atr)) 
        
        # 3. 收盘站稳: Close > MA20
        stand = self.c > self.ma20
        
        # 4. 缩量 (可选): 相比5日均量缩量
        vma5 = talib.SMA(self.v.values, 5)
        shrink_vol = self.v < vma5
        
        return (trend_up & touch & stand & shrink_vol).fillna(0).astype(int).values

    def GAP_FILLING(self):
        """
        缺口回补 (回补之前的跳空)
        逻辑：
        1. 之前(如3天内)发生过向下跳空缺口 (Gap Down: High[t-1] < Low[t-2])
        2. 今天的高点回补了该缺口 (High[t] >= Low[t-2])
        """
        # === 向下跳空缺口回补 (看多信号) ===
        # 缺口产生：昨天的最高价 < 前天的最低价
        # 注意：这里 shift(1) 是昨天，shift(2) 是前天
        gap_down = self.h.shift(1) < self.l.shift(2)
        
        # 缺口上沿压力位 (前天的最低价)
        gap_resistance = self.l.shift(2)
        
        # 今天反弹回补：今天最高价 >= 缺口压力位
        fill_up = gap_down & (self.h >= gap_resistance) & (self.c > self.o)
        
        # === 向上跳空缺口回补 (看空信号) ===
        # 缺口产生：昨天的最低价 > 前天的最高价
        gap_up = self.l.shift(1) > self.h.shift(2)
        gap_support = self.h.shift(2)
        
        # 今天下跌回补
        fill_down = gap_up & (self.l <= gap_support) & (self.c < self.o)
        
        res = np.zeros(self.n, dtype=int)
        res[fill_up] = 1
        res[fill_down] = -1
        return res

    def THREE_GOLDEN_CROSSES(self):
        """三金叉：放宽为近3日内发生，且保持多头"""
        # 1. 均线金叉 (5日上穿10日)
        ma_cross = self._cross_over(self.ma5, self.ma10)
        # 2. 均量金叉
        vol_cross = self._cross_over(self.vma5, self.vma10)
        # 3. MACD金叉
        macd_cross = self._cross_over(self.diff, self.dea)
        
        # 使用 rolling max 判断最近3天是否发生过，确保返回布尔值
        window = 3
        recent_ma = (pd.Series(ma_cross).rolling(window).max() > 0.5)
        recent_vol = (pd.Series(vol_cross).rolling(window).max() > 0.5)
        recent_macd = (pd.Series(macd_cross).rolling(window).max() > 0.5)
        
        # 且当前状态保持多头 (避免金叉后马上死叉)
        is_bull = (self.ma5 > self.ma10) & (self.vma5 > self.vma10) & (self.diff > self.dea)
        
        # 确保所有条件都是布尔型
        cond = recent_ma & recent_vol & recent_macd & is_bull
        return cond.astype(int).values

    def UPSIDE_GAP_3CROWS(self):
        return talib.CDLUPSIDEGAP2CROWS(self.o.values, self.h.values, self.l.values, self.c.values) / -100

    def POURING_RAIN(self):
        """倾盆大雨"""
        # 1. 昨天阳线
        c1 = self.c.shift(1) > self.o.shift(1)
        # 2. 今天高开
        c2 = self.o > self.c.shift(1)
        # 3. 收盘低于昨日实体中心
        mid_point = (self.o.shift(1) + self.c.shift(1)) / 2
        c3 = self.c < mid_point
        # 4. 今天是阴线
        c4 = self.c < self.o
        
        return np.where(c1 & c2 & c3 & c4, -1, 0)

    def RISING_SUN(self):
        return talib.CDLPIERCING(self.o.values, self.h.values, self.l.values, self.c.values) / 100

    def JIEDI_FANJI(self):
        """绝地反击: 长下影 + 放量 + 处于低位 (增加低位过滤以保准确)"""
        lower_shadow = np.minimum(self.o, self.c) - self.l
        body = abs(self.c - self.o)
        
        c1 = lower_shadow > body * 2
        c2 = self.v > self.vol_prev * 1.5
        c3 = self.low_pos
        
        return (c1 & c2 & c3).astype(int).values

    def DAO_BA_YANG_LIU(self):
        """倒拔杨柳: 长上影 + 放量 (通常高位看跌)"""
        upper_shadow = self.h - np.maximum(self.o, self.c)
        body = abs(self.c - self.o)
        avg_vol_5 = self.v.rolling(5).mean().shift(1)
        
        c1 = upper_shadow > body * 2
        c2 = self.v > avg_vol_5 * 2
        # c3 = self.high_pos # 可选，原文没加，但这通常是高位形态
        
        return np.where(c1 & c2, -1, 0)

    def CHU_SHUI_FU_RONG(self):
        """
        出水芙蓉 (增强版)
        1. 实体穿三线 (MA5, MA10, MA20)
        2. 必须是大阳线 (实体 > 1.5倍平均实体 或 > ATR)
        3. 放量
        """
        # 三线汇聚检查 (可选，均线不能发散得太厉害)
        ma_max = np.maximum(np.maximum(self.ma5, self.ma10), self.ma20)
        ma_min = np.minimum(np.minimum(self.ma5, self.ma10), self.ma20)
        
        # 1. 穿透: 开在最下面下面，收在最上面上面
        penetrate = (self.o < ma_min) & (self.c > ma_max)
        
        # 2. 力度: 实体长度 > 0.8 * ATR (排除掉那些波动极小的伪芙蓉)
        strong_body = (self.c - self.o) > (0.8 * self.atr)
        
        # 3. 放量: 大于5日均量
        vol_up = self.v > talib.SMA(self.v.values, 5)
        
        return (penetrate & strong_body & vol_up).fillna(0).astype(int).values

    def BACKTEST_MA5(self):
        """回踩五日线"""
        # 最低价踩破或触及 MA5，收盘站上，且价格上涨
        c1 = self.l <= self.ma5
        c2 = self.c > self.ma5
        c3 = self.c > self.close_prev
        
        return (c1 & c2 & c3).astype(int).values

    def FIVE_LINES_BLOOM(self):
        """五线开花"""
        # 均线多头排列
        c1 = (self.ma5 > self.ma10) & (self.ma10 > self.ma20) & \
             (self.ma20 > self.ma30) & (self.ma30 > self.ma60)
        # 均线向上
        c2 = self.ma5 > pd.Series(self.ma5).shift(1)
        
        return (c1 & c2).astype(int).values

    def BOTTOM_SINGLE_PEAK(self):
        """底部单峰"""
        # 10日内最大量
        max_vol_10 = self.v.rolling(10).max()
        c1 = self.v == max_vol_10
        # 价格滞涨 (波动小)
        c2 = (abs(self.c - self.o) / self.c) < 0.02
        # 低位
        c3 = self.low_pos
        
        return (c1 & c2 & c3).astype(int).values

    def DUO_FANG_PAO(self):
        """多方炮: 阳-阴-阳"""
        c1 = self.c.shift(2) > self.o.shift(2) # 前前 阳
        c2 = self.c.shift(1) < self.o.shift(1) # 前 阴
        c3 = self.c > self.o                   # 今 阳
        c4 = self.c > self.c.shift(2)          # 收盘创新高
        
        return (c1 & c2 & c3 & c4).astype(int).values

    def LONG_TENG_LOW(self):
        """龙腾四海低位"""
        rsi = talib.RSI(self.c.values, 14)
        c1 = self.low_pos
        c2 = pd.Series(rsi).shift(1) < 30
        c3 = rsi > pd.Series(rsi).shift(1)
        
        return (c1 & c2 & c3).fillna(0).astype(int).values

    def DEATH_VALLEY(self):
        """死亡谷: 均线空头死叉"""
        c1 = self._cross_under(self.ma5, self.ma10)
        c2 = self.ma10 < self.ma20
        return np.where(c1 & c2, -1, 0)

    def SILVER_VALLEY(self):
        """银山谷: 均线多头金叉"""
        c1 = self._cross_over(self.ma5, self.ma10)
        c2 = self.ma10 > self.ma20
        return (c1 & c2).astype(int).values

    def BOTTOM_REVERSAL(self):
        return talib.CDLMORNINGSTAR(self.o.values, self.h.values, self.l.values, self.c.values) / 100

    def SHORT_TERM_BULL(self):
        cond = (self.ma5 > self.ma10) & (self.ma10 > self.ma20)
        return cond.astype(int)

    def JU_BAO_PEN(self):
        """聚宝盆"""
        c1 = self.low_pos
        c2 = self.v > self.vma20
        # 过去5天不跌 (每天close >= 前一天close)
        c3 = (self.c >= self.close_prev).rolling(5).sum() == 5
        
        return (c1 & c2 & c3).fillna(0).astype(int).values

    def QIU_YING_JIN_BO(self):
        """秋影金波: 高位十字星"""
        doji = talib.CDLDOJI(self.o.values, self.h.values, self.l.values, self.c.values)
        return np.where((doji != 0) & self.high_pos, -1, 0)

    def SOLDIER_ASSAULT(self):
        """士兵突击: 三连小阳"""
        is_small_yang = (self.c > self.o) & (self.c > self.close_prev)
        count = is_small_yang.rolling(3).sum()
        return (count == 3).astype(int).values

    def BULL_PIONEER(self):
        """多头尖兵"""
        # T-4 是长阳
        long_yang = (self.c.shift(4) - self.o.shift(4)) / self.o.shift(4) > 0.04
        # 中间3天回调不破长阳开盘价
        min_low_3 = self.l.rolling(4).min() # 包括今天
        support = min_low_3 > self.o.shift(4)
        
        return (long_yang & support).fillna(0).astype(int).values

    def LOW_BIG_YANG(self):
        """低位大阳"""
        is_big = (self.c - self.o) / self.o > 0.05
        return (is_big & self.low_pos).astype(int).values

    def SHRINK_VOL_HIGH(self):
        """缩量拉高"""
        c1 = self.c > self.close_prev
        c2 = self.v < self.vol_prev * 0.7
        return np.where(c1 & c2, -1, 0)

    def QING_LONG_WATER(self):
        """青龙取水"""
        c1 = self.l <= self.ma60
        c2 = self.c > self.ma60
        c3 = self.low_pos
        return (c1 & c2 & c3).astype(int).values

    def TWO_BLACK_ONE_RED(self):
        """两黑夹一红 (空方炮)"""
        c1 = self.c.shift(2) < self.o.shift(2) # 阴
        c2 = self.c.shift(1) > self.o.shift(1) # 阳
        c3 = self.c < self.o                   # 阴
        return np.where(c1 & c2 & c3, -1, 0)

    def POOL_DRAGON(self):
        """池底巨龙"""
        # 长期横盘 (标准差小)
        std_30 = self.c.rolling(30).std()
        c1 = (std_30 / self.c) < 0.02
        # 放量突破
        c2 = (self.c - self.o) / self.o > 0.04
        
        return (c1 & c2).fillna(0).astype(int).values

    def BOTTOM_ACCUMULATION(self):
        """底部吸筹"""
        c1 = self.low_pos
        c2 = self.v > self.vma5
        # 价格变动小
        c3 = abs(self.c - self.close_prev) / self.close_prev < 0.01
        return (c1 & c2 & c3).fillna(0).astype(int).values

    def HUGE_VOL_LONG_YIN(self):
        """巨量长阴"""
        is_long_yin = (self.o - self.c) / self.o > 0.05
        # 10日均量的2倍
        avg_vol_10 = self.v.rolling(10).mean()
        is_huge_vol = self.v > avg_vol_10 * 2
        return np.where(is_long_yin & is_huge_vol, -1, 0)

    def FAKE_YANG_DOJI(self):
        """假阳十字星"""
        # 假阳: 收盘 > 开盘，但 收盘 < 昨收
        fake_yang = (self.c > self.o) & (self.c < self.close_prev)
        # 十字星: 实体极小
        is_doji = abs(self.c - self.o) / (self.h - self.l) < 0.1
        return np.where(fake_yang & is_doji, -1, 0)

    def DOLPHIN_MOUTH(self):
        """海豚嘴"""
        # MA20 向上
        c1 = self.ma20 > pd.Series(self.ma20).shift(1)
        # MA5 回踩 MA20 (之前在上方，现在接近或下方)
        prev_above = pd.Series(self.ma5).shift(1) > pd.Series(self.ma20).shift(1)
        curr_touch = self.ma5 <= self.ma20 * 1.01 # 允许1%误差
        
        return (c1 & prev_above & curr_touch).fillna(0).astype(int).values

    def MA_ADHESION(self):
        """均线粘合"""
        arrs = np.vstack([self.ma5, self.ma10, self.ma20, self.ma30])
        max_vals = np.max(arrs, axis=0)
        min_vals = np.min(arrs, axis=0)
        # 极差 < 1%
        cond = (max_vals - min_vals) / min_vals < 0.01
        return cond.astype(int)

    def BOX_BREAKOUT(self):
        """箱体突破"""
        box_high = self.h.rolling(20).max().shift(1)
        c1 = self.c > box_high
        c2 = (self.c - self.o) / self.o > 0.03
        return (c1 & c2).fillna(0).astype(int).values

    def LOOKING_BACK_MOON(self):
        """回头望月"""
        # 5天前大涨
        prev_pump = (self.c.shift(5) - self.o.shift(5)) / self.o.shift(5) > 0.05
        # 回调至均线
        touch_ma = self.l <= self.ma20
        # 缩量
        shrink_vol = self.v < self.v.shift(5)
        
        return (prev_pump & touch_ma & shrink_vol).fillna(0).astype(int).values

    def SOARING_SKY(self):
        """一飞冲天: 跳空长阳"""
        gap_up = self.o > self.h.shift(1)
        long_yang = (self.c - self.o) / self.o > 0.07
        return (gap_up & long_yang).fillna(0).astype(int).values

    def MA_RESONANCE(self):
        """均线共振"""
        c1 = self.ma5 > pd.Series(self.ma5).shift(1)
        c2 = self.ma10 > pd.Series(self.ma10).shift(1)
        c3 = self.ma20 > pd.Series(self.ma20).shift(1)
        c4 = self.ma60 > pd.Series(self.ma60).shift(1)
        return (c1 & c2 & c3 & c4).fillna(0).astype(int).values

    def WARRIOR_BREAK_WRIST(self):
        """壮士断腕"""
        # 昨破位大阴
        c1 = self.c.shift(1) < pd.Series(self.ma20).shift(1)
        c2 = (self.o.shift(1) - self.c.shift(1)) / self.o.shift(1) > 0.05
        # 今反弹阳线
        c3 = self.c > self.o
        return (c1 & c2 & c3).fillna(0).astype(int).values

    def COMEBACK(self):
        """卷土重来 (V反)"""
        c1 = self.c.shift(2) < self.c.shift(3) # 跌
        c2 = self.c > self.o                  # 涨
        c3 = self.c > self.c.shift(2)         # 包过
        return (c1 & c2 & c3).fillna(0).astype(int).values

    def XIAO_XIAO_MU_YU(self):
        """潇潇暮雨"""
        # 连续3天阴线
        is_yin = self.c < self.o
        all_yin = is_yin.rolling(4).sum() == 4
        return (all_yin & self.low_pos).fillna(0).astype(int).values

    def CLOUD_MAP(self):
        """目送云图"""
        doji = talib.CDLDOJI(self.o.values, self.h.values, self.l.values, self.c.values)
        doji_count = pd.Series(doji).rolling(4).apply(lambda x: np.sum(x != 0), raw=True)
        return np.where((doji_count >= 2) & self.high_pos, -1, 0)

    def AMBUSH(self):
        """十面埋伏"""
        # 振幅小
        amp = (self.h.rolling(6).max() - self.l.rolling(6).min()) / self.c
        c1 = amp < 0.03
        return np.where(self.high_pos & c1, -1, 0)

    def TWISTS_TURNS(self):
        return talib.CDLHARAMI(self.o.values, self.h.values, self.l.values, self.c.values) / 100

    def CLOUD_WALK(self):
        """云行雨步"""
        c1 = abs(self.c - self.ma20) / self.ma20 < 0.01
        return c1.astype(int).values

    def CURTAIN_WATERFALL(self):
        """垂帘瀑布"""
        # 连续4天收盘价降低
        c1 = self.c < self.close_prev
        seq = c1.rolling(4).sum() == 4
        return np.where(seq, -1, 0)

    def CANDLE_SHADOW_RED(self):
        """烛影摇红"""
        up_shadow = self.h - self.c
        body = self.c - self.o
        c1 = (up_shadow > body * 2) & (body > 0)
        return np.where(c1 & self.high_pos, -1, 0)

    def FLAT_TOP_PEAK(self):
        """平顶尖峰"""
        # 两个最高价几乎相同
        c1 = abs(self.h - self.h.shift(1)) / self.h < 0.002
        return np.where(c1 & self.high_pos, -1, 0)

    def ROLLING_TIDES(self):
        """万里卷潮"""
        c1 = (self.c - self.o) / self.o > 0.08
        avg_vol = self.v.rolling(10).mean().shift(1)
        c2 = self.v > avg_vol * 3
        return (c1 & c2).fillna(0).astype(int).values

    def LIGHTNING_ROD(self):
        """避雷塔针"""
        up_shadow = self.h - self.o
        body = self.o - self.c
        c1 = (up_shadow > body * 2) & (self.c < self.o)
        return np.where(c1, -1, 0)

    def FLOWER_FRUIT(self):
        """开花结果"""
        # 昨涨停
        c1 = (self.close_prev - self.c.shift(2)) / self.c.shift(2) > (self.limit_threshold - 0.005)
        # 今十字星
        c2 = abs(self.c - self.o) / self.c < 0.01
        return (c1 & c2).fillna(0).astype(int).values

    def RAIN_CLEAR_EVENING(self):
        """雨晴烟晚"""
        c1 = self.low_pos
        c2 = self.v < self.vol_prev
        c3 = abs(self.c - self.o) / self.c < 0.005
        return (c1 & c2 & c3).astype(int).values

    def WEST_WIND_SUNSET(self):
        """西风残照"""
        c1 = self.high_pos
        c2 = self.c < self.o
        c3 = self.v > self.vol_prev
        return np.where(c1 & c2 & c3, -1, 0)

    def BOTTOM_RAISING(self):
        """底部抬高"""
        # 低点依次抬高 (T, T-5, T-10)
        c1 = (self.l > self.l.shift(5)) & (self.l.shift(5) > self.l.shift(10))
        return c1.fillna(0).astype(int).values

    def FIVE_YANG_LINES(self):
        """低档五阳线"""
        is_yang = self.c > self.o
        c1 = is_yang.rolling(5).sum() == 5
        return (c1 & self.low_pos).astype(int).values

    def ROUNDING_BOTTOM(self):
        """圆弧底 (向量化简化)"""
        # 两头高，中间低
        w = 20
        mid = w // 2
        # T和T-20的价格 都高于 T-10
        c1 = (self.c > self.c.shift(mid)) & (self.c.shift(w) > self.c.shift(mid))
        return c1.fillna(0).astype(int).values

    def BACK_LIGHT(self):
        """回光返照"""
        c1 = self.c > self.o # 反弹
        c2 = self.h >= self.ma20 # 触碰压力
        c3 = self.c < self.ma20 # 收盘未站稳
        return np.where(c1 & c2 & c3, -1, 0)

    def LIMIT_UP_HORSE(self):
        """
        涨停回马枪
        1. 基因: T-N (3~7天前) 曾出现涨停
        2. 回调: 之后缩量回调，不破涨停阳线的开盘价(或中点)
        3. 启动: 今天再次放量/上涨
        """
        threshold = self.limit_threshold - 0.005 # 容差
        
        # 1. 寻找涨停基因 (过去3到7天内有一天是涨停的)
        pct = self.c.pct_change()
        is_limit_up = pct > threshold
        
        # 构建一个mask，表示"过去3-7天内有过涨停"
        # shift(3) 表示3天前...
        has_limit_genes = (is_limit_up.shift(3) | is_limit_up.shift(4) | 
                           is_limit_up.shift(5) | is_limit_up.shift(6) | is_limit_up.shift(7))
        
        # 2. 支撑位判定
        # 简单处理：过去7天最低价 >= 过去7天最低那个收盘价 (或者20日线)
        # 更精细处理：获取最近那个涨停日的 Open Price。向量化比较困难。
        # 替代方案：价格维持在 MA20 之上，且没有暴跌(单日跌幅 < 5%)
        no_crash = (pct > -0.05).rolling(7).sum() == 7
        trend_ok = self.l > self.ma20
        
        # 3. 缩量回调后启动
        # 今天上涨，且量能比昨天大
        start = (self.c > self.o) & (self.v > self.v.shift(1))
        
        return (has_limit_genes & no_crash & trend_ok & start).fillna(0).astype(int).values

    def RISING_CHANNEL(self):
        """上升通道"""
        # 5日线连续10天向上
        ma5_diff = pd.Series(self.ma5).diff()
        c1 = (ma5_diff > 0).rolling(10).sum() == 10
        return c1.fillna(0).astype(int).values

    def PLATFORM_BREAKOUT(self):
        """平台突破"""
        # 15天波动小
        std = self.c.rolling(15).std()
        mean = self.c.rolling(15).mean()
        c1 = (std / mean).shift(1) < 0.015
        # 突破前15天最高
        c2 = self.c > self.h.rolling(15).max().shift(1)
        return (c1 & c2).fillna(0).astype(int).values

    def MODERATE_VOL_INC(self):
        """温和放量"""
        ratio = self.v / pd.Series(self.vma5).shift(1)
        return ((ratio > 1.1) & (ratio < 2.0)).fillna(0).astype(int).values

    def SHRINK_VOL_RISE(self):
        return ((self.c > self.close_prev) & (self.v < self.vol_prev)).astype(int).values

    def HIGH_VOL_RISE(self):
        return ((self.c > self.close_prev) & (self.v > self.vol_prev)).astype(int).values

    def FALLING_CHANNEL(self):
        ma5_diff = pd.Series(self.ma5).diff()
        c1 = (ma5_diff < 0).rolling(10).sum() == 10
        return np.where(c1, -1, 0)

    def PLATFORM_CONSOLIDATION(self):
        std = self.c.rolling(11).std()
        mean = self.c.rolling(11).mean()
        return ((std / mean) < 0.01).fillna(0).astype(int).values

    def BEAR_ARRANGEMENT(self):
        cond = (self.ma5 < self.ma10) & (self.ma10 < self.ma20)
        return np.where(cond, -1, 0)

    def HIGH_SIDEWAYS(self):
        std = self.c.rolling(11).std()
        c1 = (std / self.c) < 0.015
        return np.where(c1 & self.high_pos, -1, 0)

    def IMMORTAL_POINT_WAY(self):
        """仙人指路"""
        up_shadow = self.h - np.maximum(self.o, self.c)
        body = abs(self.c - self.o)
        c1 = up_shadow > body * 2
        c2 = self.c > self.o
        return (c1 & c2).astype(int).values

    def OLD_DUCK_HEAD(self):
        """
        老鸭头 (严格时序版)
        1. 长期趋势: MA60 连续向上
        2. 形成鸭头: 之前发生过死叉 (Dead Cross)
        3. 形成鸭嘴: 最近发生金叉 (Golden Cross)
        4. 时序: 死叉时间 < 金叉时间
        5. 支撑: 整个过程价格未有效跌破 MA60
        """
        # 将numpy数组转换为pandas Series
        ma60_series = pd.Series(self.ma60)
        ma5_series = pd.Series(self.ma5)
        ma10_series = pd.Series(self.ma10)
        
        # 1. MA60 趋势向上 (最近10天)
        ma60_up = (self.ma60 > ma60_series.shift(1)).rolling(10).sum() == 10
        
        # 2. 交叉信号
        # prev <= prev AND curr > curr
        gold_cross = (self.ma5 > self.ma10) & (ma5_series.shift(1) <= ma10_series.shift(1))
        dead_cross = (self.ma5 < self.ma10) & (ma5_series.shift(1) >= ma10_series.shift(1))
        
        # 3. 记录最近一次交叉发生的"时间" (使用 integer index)
        # 创建一个自然数序列 [0, 1, 2, ... n]
        idx_series = pd.Series(np.arange(self.n), index=self.c.index)
        
        # 如果发生死叉，记录 index，否则 NaN，然后向前填充
        last_dead_idx = idx_series.where(dead_cross).ffill()
        last_gold_idx = idx_series.where(gold_cross).ffill()
        
        # 4. 判定逻辑
        # A: 今天必须是金叉 (鸭嘴张开)
        cond_today_gold = gold_cross
        
        # B: 最近一次死叉发生在金叉之前 (且距离不远，比如20天内)
        # 注意：因为 cond_today_gold 为 True，last_gold_idx 就是今天
        diff_days = last_gold_idx - last_dead_idx
        cond_sequence = (diff_days > 0) & (diff_days < 20)
        
        # C: 回调过程缩量 (死叉到金叉期间，均量减少) - 可选，这里简化为价格支撑
        # D: 价格在 MA60 之上 (容忍度 1%)
        price_support = self.l > (self.ma60 * 0.99)
        
        return (ma60_up & cond_today_gold & cond_sequence & price_support).fillna(0).astype(int).values

    def TOP_VOL_SPIKE(self):
        """顶部放量"""
        mean_vol = self.v.rolling(10).mean().shift(1)
        c1 = self.v > mean_vol * 2.5
        return np.where(c1 & self.high_pos, -1, 0)

    def ROCKET_LAUNCH(self):
        """火箭升空"""
        c1 = (self.c - self.o) / self.o > 0.06
        c2 = self.v > self.vol_prev * 2
        return (c1 & c2).astype(int).values
    
    def CRANE_POINTER(self):
        """仙鹤指针：仙人指路变体"""
        return self.IMMORTAL_POINT_WAY()

    def GOLDEN_SPIDER(self):
        """金蜘蛛"""
        # 三线距离非常近
        arrs = np.vstack([self.ma5, self.ma10, self.ma20])
        diff = np.max(arrs, axis=0) - np.min(arrs, axis=0)
        c1 = diff / self.c < 0.01
        # 均向上
        c2 = (self.ma5 > pd.Series(self.ma5).shift(1)) & \
             (self.ma10 > pd.Series(self.ma10).shift(1)) & \
             (self.ma20 > pd.Series(self.ma20).shift(1))
        return (c1 & c2).fillna(0).astype(int).values