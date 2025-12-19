import talib
import numpy as np
import pandas as pd

class PatternDetector:
    def __init__(self, open_p, high_p, low_p, close_p, volume, limit_threshold=0.098):
        """
        :param open_p: 开盘价 (Series/Array)
        :param high_p: 最高价
        :param low_p: 最低价
        :param close_p: 收盘价
        :param volume: 成交量
        :param limit_threshold: 涨跌停阈值，默认0.098
        """
        # 统一转为 Pandas Series 以利用 shift/rolling 等便捷功能，计算时转 numpy
        self.o = pd.Series(open_p)
        self.h = pd.Series(high_p)
        self.l = pd.Series(low_p)
        self.c = pd.Series(close_p)
        self.v = pd.Series(volume)
        self.idx = self.c.index
        self.n = len(self.c)
        self.limit_threshold = limit_threshold
        
        # === 预计算常用指标 (避免在每个函数中重复计算) ===
        self._precalculate_indicators()

    def _precalculate_indicators(self):
        # 均线
        self.ma5 = talib.SMA(self.c.values, 5)
        self.ma10 = talib.SMA(self.c.values, 10)
        self.ma20 = talib.SMA(self.c.values, 20)
        self.ma30 = talib.SMA(self.c.values, 30)
        self.ma60 = talib.SMA(self.c.values, 60)
        
        # 均量线
        self.vma5 = talib.SMA(self.v.values, 5)
        self.vma10 = talib.SMA(self.v.values, 10)
        self.vma20 = talib.SMA(self.v.values, 20)
        
        # MACD
        self.diff, self.dea, self.macd_hist = talib.MACD(self.c.values)
        
        # 基础形态数据
        self.close_prev = self.c.shift(1).fillna(0)
        self.open_prev = self.o.shift(1).fillna(0)
        self.vol_prev = self.v.shift(1).fillna(0)
        
        # 实体大小与方向
        self.is_yang = self.c > self.o
        self.is_yin = self.c < self.o
        self.body_size = abs(self.c - self.o)
        self.pct_change = (self.c - self.close_prev) / self.close_prev
        
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
        """双重底: 向量化近似实现"""
        # 寻找局部低点: 比前后各3天都低
        window = 3
        is_local_min = (self.l == self.l.rolling(window*2+1, center=True).min())
        
        results = np.zeros(self.n, dtype=int)
        
        # 获取最近一次局部低点的位置 (shift 1 排除自己)
        last_min_pos = pd.Series(np.where(is_local_min, range(self.n), np.nan)).ffill().shift(1).astype(float)
        
        # 获取该位置的低点价格 - 使用整数索引并处理NaN
        last_min_val = np.full(self.n, np.nan)
        valid_pos = last_min_pos.notna()
        if np.any(valid_pos):
            last_min_val[valid_pos] = self.l.iloc[last_min_pos[valid_pos].astype(int)].values
        
        # 颈线确认: 收盘价突破两底之间的最高价 (简化处理：突破最近20天新高)
        breakout = self.c > self.h.rolling(20).max().shift(1)
        
        # 条件：
        # 1. 之前有低点
        # 2. 两个低点差距 < 2%
        # 3. 两个低点间隔 > 5天 (避免并在)
        # 4. 当前突破
        
        dist = abs(self.l - last_min_val) / last_min_val
        days_diff = self.idx - last_min_pos
        
        # 确保所有条件值为布尔型，排除NaN
        cond1 = valid_pos
        cond2 = (dist < 0.03)
        cond3 = (days_diff > 5) & (days_diff < 60)
        cond4 = breakout
        
        cond = cond1 & cond2 & cond3 & cond4
        return cond.astype(int).values

    def DRAGONFLY_TOUCH_WATER(self):
        """蜻蜓点水"""
        # 回调至MA20不破 (最低价击穿或接近，收盘价在上方)
        # 1.005 系数允许微小刺穿或未触及
        cond1 = (self.l <= self.ma20 * 1.005) & (self.c > self.ma20)
        # 缩量
        cond2 = self.v < self.vol_prev
        # 趋势向上 (MA20 向上)
        cond3 = self.ma20 > pd.Series(self.ma20).shift(1)
        
        return (cond1 & cond2 & cond3).astype(int).values

    def GAP_FILLING(self):
        """缺口回补"""
        res = np.zeros(self.n, dtype=int)
        # 向上补: 今天低点 <= 昨天收盘 < 今天开盘 (且昨天是跳空高开) -> 实际上补缺口意味着 Gap 被填平
        # 原始逻辑：open > prev_close (高开), low <= prev_close (回补)
        up_fill = (self.o > self.close_prev) & (self.l <= self.close_prev)
        # 向下补
        down_fill = (self.o < self.close_prev) & (self.h >= self.close_prev)
        
        res[up_fill] = 1
        res[down_fill] = -1
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
        """出水芙蓉: 一阳穿三线"""
        # 开盘在三线之下
        min_ma = np.minimum(np.minimum(self.ma5, self.ma10), self.ma20)
        max_ma = np.maximum(np.maximum(self.ma5, self.ma10), self.ma20)
        
        c1 = self.o < min_ma
        c2 = self.c > max_ma
        c3 = self.c > self.o # 阳线
        
        return (c1 & c2 & c3).astype(int).values

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
        """涨停回马枪"""
        # T-5 涨停
        c1 = (self.c.shift(5) - self.c.shift(6)) / self.c.shift(6) > (self.limit_threshold - 0.005)
        # 之后几天回调不破 T-5 的收盘
        min_close = self.c.rolling(5).min() # 含今天
        c2 = min_close > self.c.shift(5)
        return (c1 & c2).fillna(0).astype(int).values

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
        老鸭头 (高度复杂形态的向量化逼近)
        逻辑拆解:
        1. 鸭颈: MA60 持续向上
        2. 鸭头: MA5 与 MA10 死叉 (Dead Cross)
        3. 鸭嘴: MA5 与 MA10 金叉 (Golden Cross) - 当前信号
        4. 支撑: 整个过程价格在 MA60 上方
        """
        # 状态1: MA60 向上 (持续一段时间，比如10天)
        ma60_up = (self.ma60 > pd.Series(self.ma60).shift(1)).rolling(10).sum() == 10
        
        # 状态2: 刚刚金叉 (鸭嘴张开)
        golden_cross = self._cross_over(self.ma5, self.ma10)
        
        # 状态3: 过去一段时间 (比如5-20天前) 有过死叉 (形成鸭头)
        dead_cross = self._cross_under(self.ma5, self.ma10)
        has_dead_cross = pd.Series(dead_cross).rolling(window=20, min_periods=5).max()
        
        # 状态4: 价格始终在 MA60 之上 (保持多头)
        above_ma60 = (self.c > self.ma60).rolling(20).sum() == 20
        
        return (ma60_up & golden_cross & has_dead_cross & above_ma60).fillna(0).astype(int).values

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