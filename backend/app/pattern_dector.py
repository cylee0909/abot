import talib
from app.custom_pattern import CustomPatternDetector

class Pattern:
    """K线形态类，用于表示单个K线形态的信息和检测方法"""
    def __init__(self, code, name, func):
        self.code = code  # 形态代码
        self.name = name  # 中文名称
        self.func = func  # 检测函数

class PatternDector:
    def __init__(self, o, h, l, c, v):
        # 存储价格和成交量数据
        self.o = o
        self.h = h
        self.l = l
        self.c = c
        self.v = v
        
        # 初始化 PatternDetector 对象
        self.pattern_detector = CustomPatternDetector(o, h, l, c, v)
        
        # 创建所有形态对象
        self._create_patterns()

    def _create_patterns(self):
        """创建所有K线形态对象"""
        # 定义TALib形态列表：(形态代码, 中文名称, 函数)
        talib_patterns_data = [
            ('CDL2CROWS', '两只乌鸦', talib.CDL2CROWS),
            ('CDL3BLACKCROWS', '三只乌鸦', talib.CDL3BLACKCROWS),
            ('CDL3INSIDE', '三内升/降', talib.CDL3INSIDE),
            ('CDL3LINESTRIKE', '三线打击', talib.CDL3LINESTRIKE),
            ('CDL3OUTSIDE', '三外升/降', talib.CDL3OUTSIDE),
            ('CDL3STARSINSOUTH', '南方三星', talib.CDL3STARSINSOUTH),
            ('CDL3WHITESOLDIERS', '三个白兵', talib.CDL3WHITESOLDIERS),
            ('CDLABANDONEDBABY', '弃婴', talib.CDLABANDONEDBABY),
            ('CDLADVANCEBLOCK', '前进受阻', talib.CDLADVANCEBLOCK),
            ('CDLBELTHOLD', '捉腰带线', talib.CDLBELTHOLD),
            ('CDLBREAKAWAY', '脱离', talib.CDLBREAKAWAY),
            ('CDLCLOSINGMARUBOZU', '收盘缺影线', talib.CDLCLOSINGMARUBOZU),
            ('CDLCONCEALBABYSWALL', '藏婴吞没', talib.CDLCONCEALBABYSWALL),
            ('CDLCOUNTERATTACK', '反击线', talib.CDLCOUNTERATTACK),
            ('CDLDARKCLOUDCOVER', '乌云盖顶', talib.CDLDARKCLOUDCOVER),
            ('CDLDOJI', '十字星', talib.CDLDOJI),
            ('CDLDOJISTAR', '十字星', talib.CDLDOJISTAR),
            ('CDLDRAGONFLYDOJI', '蜻蜓十字', talib.CDLDRAGONFLYDOJI),
            ('CDLENGULFING', '吞噬模式', talib.CDLENGULFING),
            ('CDLEVENINGDOJISTAR', '黄昏十字星', talib.CDLEVENINGDOJISTAR),
            ('CDLEVENINGSTAR', '黄昏之星', talib.CDLEVENINGSTAR),
            ('CDLGAPSIDESIDEWHITE', '向上/向下跳空并列阳线', talib.CDLGAPSIDESIDEWHITE),
            ('CDLGRAVESTONEDOJI', '墓碑十字星', talib.CDLGRAVESTONEDOJI),
            ('CDLHAMMER', '锤头', talib.CDLHAMMER),
            ('CDLHANGINGMAN', '吊颈', talib.CDLHANGINGMAN),
            ('CDLHARAMI', '孕线', talib.CDLHARAMI),
            ('CDLHARAMICROSS', '十字孕线', talib.CDLHARAMICROSS),
            ('CDLHIGHWAVE', '长影线', talib.CDLHIGHWAVE),
            ('CDLHIKKAKE', '陷阱', talib.CDLHIKKAKE),
            ('CDLHIKKAKEMOD', '修正陷阱', talib.CDLHIKKAKEMOD),
            ('CDLHOMINGPIGEON', '归巢鸽', talib.CDLHOMINGPIGEON),
            ('CDLIDENTICAL3CROWS', '三乌鸦', talib.CDLIDENTICAL3CROWS),
            ('CDLINNECK', '颈内线', talib.CDLINNECK),
            ('CDLINVERTEDHAMMER', '倒锤头', talib.CDLINVERTEDHAMMER),
            ('CDLKICKING', '反冲', talib.CDLKICKING),
            ('CDLKICKINGBYLENGTH', '反冲 - 由较长的缺影线决定多/空', talib.CDLKICKINGBYLENGTH),
            ('CDLLADDERBOTTOM', '梯底', talib.CDLLADDERBOTTOM),
            ('CDLLONGLEGGEDDOJI', '长脚十字', talib.CDLLONGLEGGEDDOJI),
            ('CDLLONGLINE', '长蜡烛', talib.CDLLONGLINE),
            ('CDLMARUBOZU', '缺影线', talib.CDLMARUBOZU),
            ('CDLMATCHINGLOW', '相同低价', talib.CDLMATCHINGLOW),
            ('CDLMATHOLD', '马特 holde', talib.CDLMATHOLD),
            ('CDLMORNINGDOJISTAR', '早晨十字星', talib.CDLMORNINGDOJISTAR),
            ('CDLMORNINGSTAR', '早晨之星', talib.CDLMORNINGSTAR),
            ('CDLONNECK', '颈上线', talib.CDLONNECK),
            ('CDLPIERCING', '贯穿模式', talib.CDLPIERCING),
            ('CDLRICKSHAWMAN', '人力车', talib.CDLRICKSHAWMAN),
            ('CDLRISEFALL3METHODS', '上升/下降三法', talib.CDLRISEFALL3METHODS),
            ('CDLSEPARATINGLINES', '分离线', talib.CDLSEPARATINGLINES),
            ('CDLSHOOTINGSTAR', '射击之星', talib.CDLSHOOTINGSTAR),
            ('CDLSHORTLINE', '短蜡烛', talib.CDLSHORTLINE),
            ('CDLSPINNINGTOP', '纺锤线', talib.CDLSPINNINGTOP),
            ('CDLSTALLEDPATTERN', '停顿形态', talib.CDLSTALLEDPATTERN),
            ('CDLSTICKSANDWICH', 'stick sandwich', talib.CDLSTICKSANDWICH),
            ('CDLTAKURI', '探水杆（带长下影线的蜻蜓十字）', talib.CDLTAKURI),
            ('CDLTASUKIGAP', 'tasuki gap', talib.CDLTASUKIGAP),
            ('CDLTHRUSTING', '冲刺形态', talib.CDLTHRUSTING),
            ('CDLTRISTAR', '三星', talib.CDLTRISTAR),
            ('CDLUNIQUE3RIVER', '独特三川', talib.CDLUNIQUE3RIVER),
            ('CDLUPSIDEGAP2CROWS', '向上跳空两只乌鸦', talib.CDLUPSIDEGAP2CROWS),
            ('CDLXSIDEGAP3METHODS', '向上/向下跳空三法', talib.CDLXSIDEGAP3METHODS),
        ]
        
        # 定义自定义形态列表：(形态代码, 中文名称, 函数)
        custom_patterns_data = [
            ('DOUBLE_BOTTOM', '双重底', self.pattern_detector.DOUBLE_BOTTOM),
            ('DRAGONFLY_TOUCH_WATER', '蜻蜓点水', self.pattern_detector.DRAGONFLY_TOUCH_WATER),
            ('GAP_FILLING', '缺口回补', self.pattern_detector.GAP_FILLING),
            ('THREE_GOLDEN_CROSSES', '三金叉', self.pattern_detector.THREE_GOLDEN_CROSSES),
            ('UPSIDE_GAP_3CROWS', '升势三鸦', self.pattern_detector.UPSIDE_GAP_3CROWS), # 注:TALib只有跳空两只乌鸦
            ('POURING_RAIN', '倾盆大雨', self.pattern_detector.POURING_RAIN),
            ('RISING_SUN', '旭日东升', self.pattern_detector.RISING_SUN),
            ('JIEDI_FANJI', '绝地反击', self.pattern_detector.JIEDI_FANJI), 
            ('DAO_BA_YANG_LIU', '倒拔杨柳', self.pattern_detector.DAO_BA_YANG_LIU),
            ('CHU_SHUI_FU_RONG', '出水芙蓉', self.pattern_detector.CHU_SHUI_FU_RONG),       
            ('BACKTEST_MA5', '回踩五日线', self.pattern_detector.BACKTEST_MA5),
            ('FIVE_LINES_BLOOM', '五线开花', self.pattern_detector.FIVE_LINES_BLOOM),
            ('BOTTOM_SINGLE_PEAK', '底部单峰', self.pattern_detector.BOTTOM_SINGLE_PEAK),
            ('DUO_FANG_PAO', '多方炮', self.pattern_detector.DUO_FANG_PAO),
            ('LONG_TENG_LOW', '龙腾四海低位', self.pattern_detector.LONG_TENG_LOW),
            ('DEATH_VALLEY', '死亡谷', self.pattern_detector.DEATH_VALLEY),
            ('SILVER_VALLEY', '银山谷', self.pattern_detector.SILVER_VALLEY),
            ('BOTTOM_REVERSAL', '底部反转', self.pattern_detector.BOTTOM_REVERSAL),
            ('SHORT_TERM_BULL', '短线多头', self.pattern_detector.SHORT_TERM_BULL),
            ('JU_BAO_PEN', '聚宝盆', self.pattern_detector.JU_BAO_PEN),
            ('QIU_YING_JIN_BO', '秋影金波', self.pattern_detector.QIU_YING_JIN_BO),
            ('SOLDIER_ASSAULT', '士兵突击', self.pattern_detector.SOLDIER_ASSAULT),
            ('BULL_PIONEER', '多头尖兵', self.pattern_detector.BULL_PIONEER),
            ('LOW_BIG_YANG', '低位大阳', self.pattern_detector.LOW_BIG_YANG),
            ('SHRINK_VOL_HIGH', '缩量拉高', self.pattern_detector.SHRINK_VOL_HIGH),
            ('QING_LONG_WATER', '青龙取水', self.pattern_detector.QING_LONG_WATER),
            ('TWO_BLACK_ONE_RED', '两黑夹一红', self.pattern_detector.TWO_BLACK_ONE_RED),
            ('POOL_DRAGON', '池底巨龙', self.pattern_detector.POOL_DRAGON),
            ('BOTTOM_ACCUMULATION', '底部吸筹', self.pattern_detector.BOTTOM_ACCUMULATION),
            ('HUGE_VOL_LONG_YIN', '巨量长阴', self.pattern_detector.HUGE_VOL_LONG_YIN),
            ('FAKE_YANG_DOJI', '假阳十字星', self.pattern_detector.FAKE_YANG_DOJI),
            ('DOLPHIN_MOUTH', '海豚嘴', self.pattern_detector.DOLPHIN_MOUTH),
            ('MA_ADHESION', '均线粘合', self.pattern_detector.MA_ADHESION),
            ('BOX_BREAKOUT', '箱体突破', self.pattern_detector.BOX_BREAKOUT),
            ('LOOKING_BACK_MOON', '回头望月', self.pattern_detector.LOOKING_BACK_MOON),
            ('SOARING_SKY', '一飞冲天', self.pattern_detector.SOARING_SKY),
            ('MA_RESONANCE', '均线共振', self.pattern_detector.MA_RESONANCE),
            ('WARRIOR_BREAK_WRIST', '壮士断腕', self.pattern_detector.WARRIOR_BREAK_WRIST),
            ('COMEBACK', '卷土重来', self.pattern_detector.COMEBACK),
            ('XIAO_XIAO_MU_YU', '潇潇暮雨', self.pattern_detector.XIAO_XIAO_MU_YU),
            ('CLOUD_MAP', '目送云图', self.pattern_detector.CLOUD_MAP),
            ('AMBUSH', '十面埋伏', self.pattern_detector.AMBUSH),
            ('TWISTS_TURNS', '峰回路转', self.pattern_detector.TWISTS_TURNS),
            ('CLOUD_WALK', '云行雨步', self.pattern_detector.CLOUD_WALK),
            ('CURTAIN_WATERFALL', '垂帘瀑布', self.pattern_detector.CURTAIN_WATERFALL),
            ('CANDLE_SHADOW_RED', '烛影摇红', self.pattern_detector.CANDLE_SHADOW_RED),
            ('FLAT_TOP_PEAK', '平顶尖峰', self.pattern_detector.FLAT_TOP_PEAK),
            ('ROLLING_TIDES', '万里卷潮', self.pattern_detector.ROLLING_TIDES),
            ('LIGHTNING_ROD', '避雷塔针', self.pattern_detector.LIGHTNING_ROD),
            ('FLOWER_FRUIT', '开花结果', self.pattern_detector.FLOWER_FRUIT),
            ('RAIN_CLEAR_EVENING', '雨晴烟晚', self.pattern_detector.RAIN_CLEAR_EVENING),
            ('WEST_WIND_SUNSET', '西风残照', self.pattern_detector.WEST_WIND_SUNSET),
            ('BOTTOM_RAISING', '底部抬高', self.pattern_detector.BOTTOM_RAISING),
            ('FIVE_YANG_LINES', '低档五阳线', self.pattern_detector.FIVE_YANG_LINES),
            ('ROUNDING_BOTTOM', '圆弧底', self.pattern_detector.ROUNDING_BOTTOM),
            ('BACK_LIGHT', '回光返照', self.pattern_detector.BACK_LIGHT),
            ('LIMIT_UP_HORSE', '涨停回马枪', self.pattern_detector.LIMIT_UP_HORSE),
            ('RISING_CHANNEL', '上升通道', self.pattern_detector.RISING_CHANNEL),
            ('PLATFORM_BREAKOUT', '平台突破', self.pattern_detector.PLATFORM_BREAKOUT),
            ('MODERATE_VOL_INC', '温和放量', self.pattern_detector.MODERATE_VOL_INC),
            ('SHRINK_VOL_RISE', '缩量上涨', self.pattern_detector.SHRINK_VOL_RISE),
            ('HIGH_VOL_RISE', '放量上涨', self.pattern_detector.HIGH_VOL_RISE),
            ('FALLING_CHANNEL', '下降通道', self.pattern_detector.FALLING_CHANNEL),
            ('PLATFORM_CONSOLIDATION', '平台整理', self.pattern_detector.PLATFORM_CONSOLIDATION),
            ('BEAR_ARRANGEMENT', '空头排列', self.pattern_detector.BEAR_ARRANGEMENT),
            ('HIGH_SIDEWAYS', '高位横盘', self.pattern_detector.HIGH_SIDEWAYS),
            ('IMMORTAL_POINT_WAY', '仙人指路', self.pattern_detector.IMMORTAL_POINT_WAY),
            ('OLD_DUCK_HEAD', '老鸭头', self.pattern_detector.OLD_DUCK_HEAD),
            ('OLD_DUCK_HEAD_LIKE', '宽松老鸭头', self.pattern_detector.OLD_DUCK_HEAD_LIKE),
            ('TOP_VOL_SPIKE', '顶部放量', self.pattern_detector.TOP_VOL_SPIKE),
            ('ROCKET_LAUNCH', '火箭升空', self.pattern_detector.ROCKET_LAUNCH),
            ('CRANE_POINTER', '仙鹤指针', self.pattern_detector.CRANE_POINTER),
            ('GOLDEN_SPIDER', '金蜘蛛', self.pattern_detector.GOLDEN_SPIDER)
        ]
        
        # 创建TALib形态对象，以code为key的map
        self.talib_patterns = {code: Pattern(code, name, func) for code, name, func in talib_patterns_data}
        
        # 创建自定义形态对象，以code为key的map
        self.custom_patterns = {code: Pattern(code, name, func) for code, name, func in custom_patterns_data}
        
        # 合并所有形态
        self.all_patterns = list(self.talib_patterns.values()) + list(self.custom_patterns.values())
        self.all_pattern_codes = [pattern.code for pattern in self.all_patterns]
    
        # 创建形态代码到中文名称的映射
        self._pattern_chinese_names = {pattern.code: pattern.name for pattern in self.all_patterns}
    
    def get_pattern_chinese_name(self, pattern_code: str) -> str:
        """获取形态代码对应的中文名称"""
        return self._pattern_chinese_names.get(pattern_code, pattern_code)
    

    def detect_patterns(self, patterns: list = []):
        pattern_results = {}
        patterns = patterns or self.all_pattern_codes

        for pattern_code in patterns:
            pattern = None
            is_talib_pattern = False
            if self.talib_patterns.get(pattern_code):
                pattern = self.talib_patterns[pattern_code]
                is_talib_pattern = True
            elif self.custom_patterns.get(pattern_code):
                pattern = self.custom_patterns[pattern_code]
        
            if pattern:
                try:
                    if is_talib_pattern:
                        pattern_results[pattern_code] = pattern.func(self.o, self.h, self.l, self.c)
                    else:
                        pattern_results[pattern_code] = pattern.func()
                except Exception as e:
                    print(f"警告：检测形态 {pattern_code} 时发生错误: {e}")
                    continue
        return pattern_results
