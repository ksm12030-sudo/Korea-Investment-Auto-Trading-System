from api_client import KisApiClient
from config import STOCK_CODE
from logger import get_logger


logger = get_logger(__name__)


# 국내주식 현재가 조회
# 모의투자/실전 공통으로 쓰이는 경우가 많지만, 문제 생기면 KIS 문서에서 tr_id만 확인하면 됨
PRICE_TR_ID = "FHKST01010100"


def get_current_price(client: KisApiClient, stock_code: str = STOCK_CODE) -> int:
    path = "/uapi/domestic-stock/v1/quotations/inquire-price"

    params = {
        "fid_cond_mrkt_div_code": "J",   # J: 주식
        "fid_input_iscd": stock_code,    # 005930
    }

    data = client.get(
        path=path,
        tr_id=PRICE_TR_ID,
        params=params,
    )

    output = data.get("output", {})
    price_text = output.get("stck_prpr")

    if price_text is None:
        raise RuntimeError(f"Current price not found in response: {data}")

    current_price = int(price_text)

    logger.info(f"Current price for {stock_code}: {current_price}")
    return current_price