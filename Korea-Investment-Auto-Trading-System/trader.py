import time
from datetime import datetime, time as dt_time

from auth import get_access_token
from api_client import KisApiClient
from market_data import get_current_price
from account import (
    get_account_balance,
    get_samsung_holding_quantity,
    has_pending_order,
)
from orders import (
    place_limit_buy_order,
    place_limit_sell_order,
    adjust_price_to_tick,
)
from config import (
    BUY_OFFSET,
    SELL_OFFSET,
    POLL_INTERVAL_SECONDS,
    MAX_CONSECUTIVE_ERRORS,
)
from logger import get_logger


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
            logger.info("Outside trading window. No order will be placed.")
            print("현재는 거래 시간이 아니라 주문하지 않음.")
            return

        try:
            current_price = get_current_price(self.client)
            logger.info(f"Current price: {current_price}")
        except Exception as e:
            logger.error(f"Failed to get current price. Skip this cycle. Error: {e}")
            self.consecutive_errors += 1
            return

        try:
            before_balance = get_account_balance(self.client)
            before_qty = get_samsung_holding_quantity(before_balance)
        except Exception as e:
            logger.error(f"Failed to get account balance. Skip this cycle. Error: {e}")
            self.consecutive_errors += 1
            return

        logger.info(f"Samsung quantity before order: {before_qty}")

        try:
            if has_pending_order(self.client):
                logger.info("Pending order exists. Skip this cycle to avoid duplicate orders.")
                self.consecutive_errors = 0
                return
        except Exception as e:
                logger.error(f"Failed to check pending orders. Skip this cycle. Error: {e}")
                self.consecutive_errors += 1
                return

        raw_buy_price = current_price - BUY_OFFSET
        raw_sell_price = current_price + SELL_OFFSET

        buy_price = adjust_price_to_tick(raw_buy_price, "down")
        sell_price = adjust_price_to_tick(raw_sell_price, "up")

        logger.info(f"Adjusted buy price: {buy_price}")
        logger.info(f"Adjusted sell price: {sell_price}")

        try:
            buy_result = place_limit_buy_order(
                client=self.client,
                price=buy_price,
                quantity=1,
            )
        except Exception as e:
            logger.error(f"Buy order request failed. Skip this cycle. Error: {e}")
            self.consecutive_errors += 1
            return

        if is_order_success(buy_result):
            logger.info("Buy order submitted successfully.")
            time.sleep(5)

            try:
                after_buy_balance = get_account_balance(self.client)
                after_buy_qty = get_samsung_holding_quantity(after_buy_balance)
            except Exception as e:
                logger.error(f"Failed to check balance after buy order. Error: {e}")
                self.consecutive_errors += 1
                return

            logger.info(f"Samsung quantity after buy order: {after_buy_qty}")
        else:
            logger.warning(f"Buy order failed or rejected: {buy_result}")
            self.consecutive_errors = 0
            return

        # 보유 수량이 없으면 매도 주문은 넣지 않음
        if after_buy_qty <= 0:
            logger.info("No Samsung shares available. Sell order skipped.")
            self.consecutive_errors = 0
            return

        try:
            sell_result = place_limit_sell_order(
                client=self.client,
                price=sell_price,
                quantity=1,
            )
        except Exception as e:
            logger.error(f"Sell order request failed. Error: {e}")
            self.consecutive_errors += 1
            return

        if is_order_success(sell_result):
            logger.info("Sell order submitted successfully.")
            time.sleep(5)

            try:
                after_sell_balance = get_account_balance(self.client)
                after_sell_qty = get_samsung_holding_quantity(after_sell_balance)
            except Exception as e:
                logger.error(f"Failed to check balance after sell order. Error: {e}")
                self.consecutive_errors += 1
                return

            logger.info(f"Samsung quantity after sell order: {after_sell_qty}")
            self.consecutive_errors = 0
        else:
            logger.warning(f"Sell order failed or rejected: {sell_result}")
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