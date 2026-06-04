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