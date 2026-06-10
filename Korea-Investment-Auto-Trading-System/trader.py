import time
from datetime import datetime, time as dt_time

from account import get_account_balance, get_samsung_holding_quantity
from api_client import KisApiClient
from auth import get_access_token
from config import (
    BUY_OFFSET,
    SELL_OFFSET,
    POLL_INTERVAL_SECONDS,
    ORDER_CHECK_DELAY_SECONDS,
    MAX_CONSECUTIVE_ERRORS,
)
from logger import get_logger
from market_data import get_current_price
from orders import place_limit_buy_order, place_limit_sell_order, adjust_price_to_tick


logger = get_logger(__name__)

TRADING_START = dt_time(9, 10)
TRADING_END = dt_time(15, 30)


def is_trading_time() -> bool:
    now = datetime.now().time()
    return TRADING_START <= now <= TRADING_END


def is_order_success(response: dict) -> bool:
    return response.get("rt_cd") == "0"


class SamsungAutoTrader:
    def __init__(self):
        token = get_access_token()
        self.client = KisApiClient(access_token=token)
        self.consecutive_errors = 0

    def run_once(self) -> None:
        if not is_trading_time():
            logger.info("Outside trading time. Skip this cycle.")
            return

        # 1. 현재가 조회
        try:
            current_price = get_current_price(self.client)
            logger.info(f"Current price: {current_price}")
        except Exception as e:
            logger.error(f"Failed to get current price. Error: {e}")
            self.consecutive_errors += 1
            return

        # 2. 잔고 / 보유수량 조회
        try:
            balance = get_account_balance(self.client)
            holding_qty = get_samsung_holding_quantity(balance)
            logger.info(f"Samsung quantity before order: {holding_qty}")
        except Exception as e:
            logger.error(f"Failed to check balance before order. Error: {e}")
            self.consecutive_errors += 1
            return


        # 3. 주문 가격 계산
        raw_buy_price = current_price - BUY_OFFSET
        raw_sell_price = current_price + SELL_OFFSET

        buy_price = adjust_price_to_tick(raw_buy_price, "down")
        sell_price = adjust_price_to_tick(raw_sell_price, "up")

        logger.info(f"Adjusted buy price: {buy_price}")
        logger.info(f"Adjusted sell price: {sell_price}")

        # 4. 보유수량이 0이면 매수만 실행
        if holding_qty <= 0:
            logger.info("No Samsung shares. Submit buy order only.")

            try:
                buy_result = place_limit_buy_order(
                    client=self.client,
                    price=buy_price,
                    quantity=1,
                )
                logger.info(f"Buy order response: {buy_result}")
            except Exception as e:
                logger.error(f"Buy order request failed. Error: {e}")
                self.consecutive_errors += 1
                return

            if not is_order_success(buy_result):
                logger.warning(f"Buy order failed or rejected: {buy_result}")
                self.consecutive_errors = 0
                return

            logger.info("Buy order submitted successfully.")

            # 주문 후 잔고 재조회
            time.sleep(ORDER_CHECK_DELAY_SECONDS)

            try:
                after_buy_balance = get_account_balance(self.client)
                after_buy_qty = get_samsung_holding_quantity(after_buy_balance)
                logger.info(f"Samsung quantity after buy order: {after_buy_qty}")
            except Exception as e:
                logger.error(f"Failed to check balance after buy order. Error: {e}")
                self.consecutive_errors += 1
                return

            self.consecutive_errors = 0
            return

        # 5. 보유수량이 있으면 매수는 하지 않고 매도만 실행
        logger.info("Already holding Samsung shares. Buy order skipped. Submit sell order only.")

        try:
            sell_result = place_limit_sell_order(
                client=self.client,
                price=sell_price,
                quantity=1,
            )
            logger.info(f"Sell order response: {sell_result}")
        except Exception as e:
            logger.error(f"Sell order request failed. Error: {e}")
            self.consecutive_errors += 1
            return

        if not is_order_success(sell_result):
            logger.warning(f"Sell order failed or rejected: {sell_result}")
            self.consecutive_errors = 0
            return

        logger.info("Sell order submitted successfully.")

        # 주문 후 잔고 재조회
        time.sleep(ORDER_CHECK_DELAY_SECONDS)

        try:
            after_sell_balance = get_account_balance(self.client)
            after_sell_qty = get_samsung_holding_quantity(after_sell_balance)
            logger.info(f"Samsung quantity after sell order: {after_sell_qty}")
        except Exception as e:
            logger.error(f"Failed to check balance after sell order. Error: {e}")
            self.consecutive_errors += 1
            return

        self.consecutive_errors = 0

    def run(self) -> None:
        logger.info("Auto trader started.")

        while True:
            now = datetime.now().time()

            if now > TRADING_END:
                logger.info("Trading window ended. Auto trader stopped.")
                print("거래 시간이 끝나 자동매매를 종료함.")
                break

            if not is_trading_time():
                logger.info("Waiting for trading window...")
                print("거래 시간 전이라 대기 중...")
                time.sleep(60)
                continue

            self.run_once()

            if self.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.error("Too many consecutive errors. Auto trader stopped for safety.")
                print("연속 에러가 너무 많아서 자동매매를 종료함.")
                break

            logger.info(f"Waiting {POLL_INTERVAL_SECONDS} seconds before next cycle.")
            time.sleep(POLL_INTERVAL_SECONDS)
