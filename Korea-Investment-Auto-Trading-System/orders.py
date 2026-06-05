from typing import Any, Dict

from api_client import KisApiClient
from config import ACCOUNT_NO, ACCOUNT_PRODUCT_CODE, STOCK_CODE
from logger import get_logger


logger = get_logger(__name__)

# 모의투자 국내주식 주문 TR ID
BUY_ORDER_TR_ID = "VTTC0802U"   # 모의투자 매수
SELL_ORDER_TR_ID = "VTTC0801U"  # 모의투자 매도


def place_limit_buy_order(
    client: KisApiClient,
    stock_code: str = STOCK_CODE,
    price: int = 0,
    quantity: int = 1,
) -> Dict[str, Any]:
    if not ACCOUNT_NO:
        raise ValueError("ACCOUNT_NO is missing")

    path = "/uapi/domestic-stock/v1/trading/order-cash"

    body = {
        "CANO": ACCOUNT_NO,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "PDNO": stock_code,
        "ORD_DVSN": "00",          # 00: 지정가
        "ORD_QTY": str(quantity),
        "ORD_UNPR": str(price),
    }

    logger.info(f"Buy order request | stock={stock_code}, price={price}, qty={quantity}")

    data = client.post(
        path=path,
        tr_id=BUY_ORDER_TR_ID,
        json_body=body,
    )

    logger.info(f"Buy order response: {data}")
    return data


def place_limit_sell_order(
    client: KisApiClient,
    stock_code: str = STOCK_CODE,
    price: int = 0,
    quantity: int = 1,
) -> Dict[str, Any]:
    if not ACCOUNT_NO:
        raise ValueError("ACCOUNT_NO is missing")

    path = "/uapi/domestic-stock/v1/trading/order-cash"

    body = {
        "CANO": ACCOUNT_NO,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "PDNO": stock_code,
        "ORD_DVSN": "00",          # 00: 지정가
        "ORD_QTY": str(quantity),
        "ORD_UNPR": str(price),
    }

    logger.info(f"Sell order request | stock={stock_code}, price={price}, qty={quantity}")

    data = client.post(
        path=path,
        tr_id=SELL_ORDER_TR_ID,
        json_body=body,
    )

    logger.info(f"Sell order response: {data}")
    return data

def get_tick_size(price: int) -> int:
    if price < 2000:
        return 1
    if price < 5000:
        return 5
    if price < 20000:
        return 10
    if price < 50000:
        return 50
    if price < 200000:
        return 100
    if price < 500000:
        return 500
    return 1000


def adjust_price_to_tick(price: int, direction: str) -> int:
    tick = get_tick_size(price)

    if direction == "down":
        return price - (price % tick)

    if direction == "up":
        remainder = price % tick
        if remainder == 0:
            return price
        return price + (tick - remainder)

    raise ValueError("direction must be 'down' or 'up'")