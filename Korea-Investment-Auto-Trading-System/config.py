import os
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("GH_APPKEY")
APP_SECRET = os.getenv("GH_APPSECRET")
ACCOUNT_NO = os.getenv("GH_ACCOUNT_NO")
ACCOUNT_PRODUCT_CODE = os.getenv("GH_ACCOUNT_PRODUCT_CODE", "01")

STOCK_CODE = "005930"

# KIS 모의투자 서버 URL
BASE_URL = "https://openapivts.koreainvestment.com:29443"

BUY_OFFSET = 1000
SELL_OFFSET = 1000

TRADING_START = "09:10"
TRADING_END = "15:30"

RUN_ONCE = False

POLL_INTERVAL_SECONDS = 300
ORDER_CHECK_DELAY_SECONDS = 5
MAX_CONSECUTIVE_ERRORS = 5