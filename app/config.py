from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DB_PATH: str = "data/hs300_history.db"
    MAX_CONCURRENT: int = 20
    
    # 雪球配置（用于AKShare的部分接口）
    XUEQIU_TOKEN: str = os.getenv("XUEQIU_TOKEN", "")
    
    # 股票下载配置
    START_DATE: str = "2015-01-01"

settings = Settings()