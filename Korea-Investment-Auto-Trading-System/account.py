from typing import Any, Dict

from api_client import KisApiClient
from config import ACCOUNT_NO, ACCOUNT_PRODUCT_CODE
from logger import get_logger


logger = get_logger(__name__)

# 모의투자 국내주식 잔고조회 TR ID
# 만약 오류가 나면 KIS 문서에서 모의투자 잔고조회 TR ID를 확인해서 수정
BALANCE_TR_ID = "VTTC8434R"


def get_account_balance(client: KisApiClient) -> Dict[str, Any]:
    if not ACCOUNT_NO:
        raise ValueError("ACCOUNT_NO is missing")

    path = "/uapi/domestic-stock/v1/trading/inquire-balance"

    params = {
        "CANO": ACCOUNT_NO,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    data = client.get(
        path=path,
        tr_id=BALANCE_TR_ID,
        params=params,
    )

    holdings = data.get("output1", [])
    summary = data.get("output2", [])

    logger.info(f"Holdings count: {len(holdings)}")
    logger.info(f"Account summary: {summary}")

    return {
        "holdings": holdings,
        "summary": summary,
        "raw": data,
    }


def get_samsung_holding_quantity(balance: Dict[str, Any]) -> int:
    holdings = balance.get("holdings", [])

    for item in holdings:
        if item.get("pdno") == "005930":
            quantity_text = item.get("hldg_qty", "0")
            return int(quantity_text)

    return 0

from datetime import datetime
from typing import List


PENDING_ORDER_TR_ID = "VTTC8001R"


def get_pending_orders(client: KisApiClient) -> List[Dict[str, Any]]:
    """
    삼성전자(005930)의 당일 미체결 주문을 조회한다.
    미체결 주문이 있으면 중복 주문을 막기 위해 사용한다.
    """
    if not ACCOUNT_NO:
        raise ValueError("ACCOUNT_NO is missing")

    today = datetime.now().strftime("%Y%m%d")

    path = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"

    params = {
        "CANO": ACCOUNT_NO,
        "ACNT_PRDT_CD": ACCOUNT_PRODUCT_CODE,
        "INQR_STRT_DT": today,
        "INQR_END_DT": today,
        "SLL_BUY_DVSN_CD": "00",
        "INQR_DVSN": "00",
        "PDNO": "005930",
        "CCLD_DVSN": "02",      # 02: 미체결 조회
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "INQR_DVSN_3": "00",
        "INQR_DVSN_1": "",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    data = client.get(
        path=path,
        tr_id=PENDING_ORDER_TR_ID,
        params=params,
    )

    orders = data.get("output1", [])
    pending_orders = []

    for order in orders:
        stock_code = order.get("pdno")
        remaining_qty = int(order.get("rmn_qty", "0") or "0")

        if stock_code == "005930" and remaining_qty > 0:
            pending_orders.append(order)

    logger.info(f"Pending Samsung orders count: {len(pending_orders)}")
    return pending_orders


def has_pending_order(client: KisApiClient) -> bool:
    pending_orders = get_pending_orders(client)
    return len(pending_orders) > 0