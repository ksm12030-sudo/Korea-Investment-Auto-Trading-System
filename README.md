# 1. Project Overview

본 프로젝트는 한국투자증권 Open API의 모의투자 환경을 활용하여 삼성전자(005930)를 대상으로 한 간단한 자동매매 시스템을 구현한 프로젝트이다.

본 시스템은 REST API만 사용하며, websocket은 사용하지 않는다. 한국 주식시장 거래시간 내에서만 실행되도록 설계하였고, 삼성전자 현재가 조회, 계좌 잔고 및 보유수량 조회, 지정가 주문 제출, 주문 후 잔고 재조회 과정을 자동으로 수행한다.

이 프로젝트의 목적은 수익률을 극대화하는 투자 전략을 만드는 것이 아니라, Open API를 활용하여 자동매매 시스템의 기본 구조를 구현하고 실제 모의투자 환경에서 작동 여부를 검증하는 것이다.

## 프로젝트 목표

본 프로젝트의 주요 목표는 다음과 같다.

- 한국투자증권 Open API 인증 구현
- 삼성전자 현재가 조회
- 계좌 잔고 및 보유수량 조회
- 지정가 매수/매도 주문 제출
- 주문 후 잔고 재조회로 체결 여부 확인
- 거래시간 내에서만 자동매매 실행
- 모의투자 환경의 API 요청 제한을 고려한 안정적인 polling 구조 구현

---

# 2. Used Data

본 프로젝트는 한국투자증권 Open API의 모의투자 환경에서 제공하는 실시간 시세 데이터와 계좌 관련 데이터를 사용한다.

본 시스템에서 활용한 데이터는 다음과 같다.

| 데이터 | 설명 |
| --- | --- |
| 현재가 | 삼성전자의 최근 체결 가격 |
| 계좌 잔고 | 예수금, 평가금액, 자산 증감액 등 계좌 요약 정보 |
| 보유수량 | 계좌에 보유 중인 삼성전자 수량 |
| 매수 주문 응답 | 매수 주문 제출 후 API가 반환한 결과 |
| 매도 주문 응답 | 매도 주문 제출 후 API가 반환한 결과 |
| 주문 후 잔고 | 주문 제출 이후 다시 조회한 계좌 잔고 및 보유수량 |
| 수익률 관련 데이터 | 총 평가금액, 자산 증감액, 자산 증감률 |

### 1. 현재가 데이터

삼성전자 현재가는 국내주식 현재가 조회 API를 통해 가져온다.

```
Current price for 005930: 317250
```

### 2. 계좌 잔고 및 보유수량 데이터

계좌 잔고 조회 API를 통해 현재 계좌에 삼성전자를 보유하고 있는지 확인한다. 본 시스템은 삼성전자 보유수량을 기준으로 매수 또는 매도 여부를 결정한다.

```
Samsung quantity before order: 1
```

### 3. 주문 응답 데이터

매수 또는 매도 주문을 제출하면 API는 주문 응답을 반환한다. 응답값에서 `rt_cd = 0`이면 주문 요청이 모의투자 서버에 정상 접수되었다는 뜻이다.

```
Sell order response: {'rt_cd': '0', 'msg_cd': '40590000', 'msg1': '모의투자 매도주문이 완료 되었습니다.'}
```

다만 주문 접수 성공이 곧바로 체결 성공을 의미하지는 않는다. 따라서 본 시스템은 주문 제출 후 계좌 잔고를 다시 조회하여 체결 여부를 판단한다.

### 4. 계좌 성과 데이터

계좌 요약 정보에는 총 평가금액, 자산 증감액, 자산 증감률 등이 포함된다.

```
tot_evlu_amt: 10035849
asst_icdc_amt: 35849
asst_icdc_erng_rt: 0.35849000
```

이 값들은 자동매매 시스템 실행 결과를 설명하는 참고 지표로 사용하였다.

---

# 3. Trading Logic

초기 아이디어는 현재가를 기준으로 (현재가 - 1000) 원 가격에 매수 주문을 넣고, (현재가 + 1000)원 가격에 매도 주문을 넣는 단순 지정가 전략이었다. 그러나 매 사이클마다 매수와 매도를 모두 제출하면 모의투자 환경에서 불안정한 동작이 발생할 수 있다라는 것을 깨닫게 되었다. 

따라서 최종 구현에서는 실제 보유수량을 기준으로 매수와 매도를 분기하는 방식을 사용하였다.

## 3.1 최종 매매 로직

최종 매매 로직은 다음과 같다.

1. 현재 시간이 거래시간인지 확인한다.
2. 삼성전자 현재가를 조회한다.
3. 계좌 잔고와 삼성전자 보유수량을 조회한다.
4. 삼성전자 보유수량이 0이면 매수 주문만 제출한다.
5. 삼성전자 보유수량이 1 이상이면 추가 매수는 하지 않고 매도 주문만 제출한다.
6. 주문 제출 후 일정 시간 대기한 뒤 잔고와 보유수량을 다시 조회한다.
7. 다음 polling 주기까지 대기한다.
8. 15:30 이후에는 자동으로 종료한다.

## 3.2 매수 로직

삼성전자를 보유하고 있지 않은 경우에만 매수 주문을 제출한다.

```
보유수량 = 0
→ 매수 주문만 제출
```

매수 주문 가격은 다음과 같이 계산한다.

```
매수 주문가 = 현재가 - BUY_OFFSET
```

본 프로젝트에서는 `BUY_OFFSET`을 1000원으로 설정하였다.

예시:

```
Current price: 317250
Adjusted buy price: 316000
```

## 3.3 매도 로직

삼성전자를 보유하고 있는 경우에는 추가 매수를 하지 않고 매도 주문만 제출한다.

```
보유수량 > 0
→ 매수 스킵
→ 매도 주문만 제출
```

매도 주문 가격은 다음과 같이 계산한다.

```
매도 주문가 = 현재가 + SELL_OFFSET
```

본 프로젝트에서는 `SELL_OFFSET`을 1000원으로 설정하였다.

```
Current price: 317250
Adjusted sell price: 318500
```

## 3.4 체결 여부 확인

본 시스템은 주문 접수와 실제 체결을 구분한다. 주문 접수는 서버가 주문 요청을 받아들였다는 뜻이고, 체결은 실제로 주식이 매수되거나 매도되어 보유수량이 변했다는 뜻이다. 따라서 주문을 제출한 뒤 일정 시간 대기한 후 잔고를 다시 조회한다.

예를 들어 매도 주문 후 다음과 같이 보유수량이 0이 되면 매도 주문이 체결된 것으로 판단할 수 있다.

```
Sell order submitted successfully.
Samsung quantity after sell order: 0
```

---

# 4. Safety Design

한국투자증권 모의투자 환경은 API 요청 제한이 엄격하기 때문에, 본 프로젝트는 빠른 매매보다 안정성과 요청 최소화를 우선하였다.

### 1. 모의투자 환경 전용

본 시스템은 모의투자 환경에서만 실행되도록 설계하였다. 실전투자 환경이나 실제 자금 운용을 전제로 하지 않는다.

### 2. REST API만 사용

본 프로젝트는 polling 기반 REST API만 사용한다. Websocket은 사용하지 않는다.

### 3. Access Token 캐싱

Access token은 `token_cache.json`에 저장된다. 당일 발급된 토큰이 존재하면 새 토큰을 발급하지 않고 기존 토큰을 재사용한다. 이를 통해 불필요한 인증 요청을 줄일 수 있다.

### 4. 보수적인 Polling Interval

시스템은 매 사이클마다 일정 시간 대기한다.

```python
POLL_INTERVAL_SECONDS = 600
```

즉, 한 사이클이 끝난 뒤 10분 동안 대기한다. 이를 통해 모의투자 환경에서 과도한 API 호출을 방지한다.

### 5. 주문 후 대기 시간

주문 제출 직후 바로 잔고를 조회하지 않고 일정 시간 기다린 뒤 잔고를 다시 조회한다.

```python
ORDER_CHECK_DELAY_SECONDS = 30
```

이는 모의투자 서버가 주문 결과를 계좌 정보에 반영할 시간을 주기 위한 설정이다.

### 6. 보유수량 기반 주문 판단

본 시스템은 매 사이클마다 무조건 매수와 매도 주문을 모두 제출하지 않는다. 실제 보유수량을 기준으로 매수 또는 매도를 선택한다.

```
보유수량 없음 → 매수만
보유수량 있음 → 매도만
```

이 방식은 잔고가 없을 때 매도 주문이 거절되는 문제와, 보유 중인데 추가 매수가 반복되어 포지션이 커지는 문제를 줄인다.

### 7. 에러 처리 및 재시도

API 요청 실패, timeout, 요청 제한 오류 등이 발생할 수 있으므로, 공통 API client에서 간단한 retry 로직을 적용하였다.

### 8. 거래시간 제한

시스템은 09:10부터 15:30까지만 거래를 수행한다. 15:30 이후에는 자동으로 종료된다.

---

# 5. Project Folder Structure

```
Korea-Investment-Auto-Trading-System/
│
├── main.py
├── config.py
├── auth.py
├── api_client.py
├── market_data.py
├── account.py
├── orders.py
├── trader.py
├── logger.py
├── requirements.txt
└──.gitignore
```

---

# 6. File Explanation

| File | Responsibility |
| --- | --- |
| `main.py` | 프로그램 시작점. `SamsungAutoTrader`를 생성하고 실행 |
| `config.py` | 환경변수, 종목코드, API URL, 주문 offset, polling interval 설정 |
| `auth.py` | access token 발급 및 당일 token cache 재사용 |
| `api_client.py` | KIS API GET/POST 요청 공통 처리 |
| `market_data.py` | 삼성전자 현재가 조회 |
| `account.py` | 잔고조회, 보유수량 조회 |
| `orders.py` | 지정가 매수/매도 주문 및 호가단위 보정 |
| `trader.py` | 전체 자동매매 로직 |
| `logger.py` | 콘솔 및 파일 로그 설정 |
| `requirements.txt` | 필요한 Python 패키지 목록 |

### `main.py`

`main.py`는 프로그램의 시작점이다. `SamsungAutoTrader` 객체를 생성하고 자동매매 루프를 실행한다.

역할:

- 프로그램 실행 시작
- 자동매매 객체 생성
- 전체 trading loop 실행

### `config.py`

`config.py`는 프로젝트 전반에서 사용하는 설정값을 관리한다.

역할:

- 환경변수 로드
- API key, secret, 계좌번호 관리
- 삼성전자 종목코드 설정
- KIS 모의투자 서버 URL 설정
- 매수/매도 offset 설정
- polling interval 설정
- 주문 후 잔고 확인 대기시간 설정

주요 설정값:

```python
STOCK_CODE = "005930"
BASE_URL = "https://openapivts.koreainvestment.com:29443"

BUY_OFFSET = 1000
SELL_OFFSET = 1000

POLL_INTERVAL_SECONDS = 600
ORDER_CHECK_DELAY_SECONDS = 30
```

### `auth.py`

`auth.py`는 인증을 담당한다.

역할:

- 기존 access token 캐시 확인
- 당일 발급된 토큰이면 재사용
- 토큰이 없거나 날짜가 다르면 새 토큰 발급
- 새 토큰을 `token_cache.json`에 저장

이를 통해 불필요한 토큰 재발급을 방지한다.

### `api_client.py`

`api_client.py`는 KIS Open API 요청을 공통으로 처리하는 모듈이다.

역할:

- API 요청 header 생성
- access token, app key, app secret, TR ID 포함
- GET 요청 처리
- POST 요청 처리
- timeout 설정
- API 에러 로그 기록
- 요청 실패 시 retry 수행

이 파일을 통해 API 요청 로직과 자동매매 로직을 분리하였다.

### `market_data.py`

`market_data.py`는 시장 데이터 조회를 담당한다.

역할:

- 삼성전자 현재가 조회
- API 응답에서 현재가 필드 추출
- 현재가를 정수형으로 변환하여 반환

현재가는 매수/매도 주문가격을 계산하는 기준으로 사용된다.

### `account.py`

`account.py`는 계좌 관련 기능을 담당한다.

역할:

- 계좌 잔고 조회
- 보유 종목 목록 조회
- 삼성전자 보유수량 추출

### `orders.py`

`orders.py`는 주문 제출을 담당한다.

역할:

- 지정가 매수 주문 제출
- 지정가 매도 주문 제출
- 주문 요청 및 응답 로그 기록
- 한국 주식시장 호가단위에 맞게 주문가격 보정

### `trader.py`

`trader.py`는 자동매매의 핵심 로직을 담당한다.

역할:

- 거래시간 확인
- 현재가 조회
- 잔고 및 보유수량 조회
- 보유수량 기준 매수/매도 분기
- 주문 제출
- 주문 후 잔고 재조회
- 거래시간 내 반복 실행
- 15:30 이후 자동 종료

### `logger.py`

`logger.py`는 로그 설정을 담당한다.

역할:

- `logs/` 폴더 생성
- 콘솔 로그 출력
- `logs/trader.log` 파일에 로그 저장
- 로그 형식 통일

### `requirements.txt`

`requirements.txt`는 프로젝트 실행에 필요한 Python 패키지를 정리한 파일이다.

```
requests
python-dotenv
```

---

# 7. Code Explanation

이 섹션에서는 핵심 코드의 역할을 설명한다.

## 7.1 설정 로드

시스템은 API key와 계좌번호를 코드에 직접 작성하지 않고 환경변수에서 불러온다.

```python
APP_KEY = os.getenv("GH_APPKEY")
APP_SECRET = os.getenv("GH_APPSECRET")
ACCOUNT_NO = os.getenv("GH_ACCOUNT_NO")
ACCOUNT_PRODUCT_CODE = os.getenv("GH_ACCOUNT_PRODUCT_CODE", "01")
```

이를 통해 민감한 인증 정보를 코드에서 분리할 수 있다.

삼성전자 종목코드는 다음과 같이 설정하였다.

```python
STOCK_CODE = "005930"
```

모의투자 서버 URL은 다음과 같다.

```python
BASE_URL = "https://openapivts.koreainvestment.com:29443"
```

## 7.2 Access Token 발급 및 재사용

인증 모듈은 먼저 `token_cache.json`에 저장된 토큰이 있는지 확인한다.

```python
if data.get("date") == date.today().isoformat():
    logger.info("Reusing cached access token")
    return data.get("access_token")
```

저장된 토큰이 오늘 발급된 것이면 재사용하고, 그렇지 않으면 새 access token을 요청한다.

이 방식은 불필요한 인증 요청을 줄이는 데 도움이 된다.

## 7.3 공통 API Client

API client는 요청마다 필요한 header를 생성한다.

```python
return {
    "content-type": "application/json; charset=utf-8",
    "authorization": f"Bearer {self.access_token}",
    "appkey": APP_KEY or "",
    "appsecret": APP_SECRET or "",
    "tr_id": tr_id,
}
```

또한 API 요청 실패 시 에러를 기록하고 재시도한다.

```python
if response.status_code >= 400:
    logger.error(
        f"GET error response | status={response.status_code} | body={response.text}"
    )
```

이를 통해 일시적인 API 오류나 요청 제한 오류가 발생하더라도 프로그램이 바로 종료되지 않도록 하였다.

## 7.4 현재가 조회

현재가 조회 함수는 API 응답에서 `stck_prpr` 값을 가져온다.

```python
price_text = output.get("stck_prpr")
current_price = int(price_text)
```

이 현재가를 기준으로 매수/매도 주문 가격을 계산한다.

## 7.5 잔고 및 보유수량 조회

잔고조회 API의 응답은 보유 종목 목록과 계좌 요약 정보로 구성된다.

```python
holdings = data.get("output1", [])
summary = data.get("output2", [])
```

삼성전자 보유수량은 보유 종목 목록에서 종목코드가 `005930`인 항목을 찾아 추출한다.

```python
if item.get("pdno") == "005930":
    quantity_text = item.get("hldg_qty", "0")
    return int(quantity_text)
```

만약 삼성전자를 보유하고 있지 않으면 0을 반환한다.

## 7.6 주문 제출

매수와 매도 주문은 모두 지정가 주문으로 제출한다.

```python
ORD_DVSN = "00"
ORD_QTY = str(quantity)
ORD_UNPR = str(price)
```

매수와 매도는 서로 다른 TR ID를 사용한다.

```python
BUY_ORDER_TR_ID = "VTTC0802U"
SELL_ORDER_TR_ID = "VTTC0801U"
```

또한 주문가격이 한국 주식시장 호가단위에 맞지 않으면 주문 오류가 발생할 수 있기 때문에, 호가단위 보정 함수를 사용하였다.

```python
def adjust_price_to_tick(price: int, direction: str) -> int:
    tick = get_tick_size(price)
```

## 7.7 자동매매 핵심 로직

자동매매의 핵심 로직은 `trader.py`에 구현되어 있다.

먼저 거래시간인지 확인한다.

```python
if not is_trading_time():
    logger.info("Outside trading time. Skip this cycle.")
    return
```

그 다음 현재가를 조회하고, 계좌 잔고와 보유수량을 확인한다.

```python
current_price = get_current_price(self.client)
balance = get_account_balance(self.client)
holding_qty = get_samsung_holding_quantity(balance)
```

최종 매매 결정은 보유수량을 기준으로 한다.

보유수량이 없으면 매수 주문을 제출한다.

```python
if holding_qty <= 0:
    logger.info("No Samsung shares. Submit buy order only.")
```

보유수량이 있으면 매수는 하지 않고 매도 주문만 제출한다.

```python
logger.info("Already holding Samsung shares. Buy order skipped. Submit sell order only.")
```

주문 제출 후에는 잔고를 다시 조회하여 체결 여부를 추정한다.

```python
after_sell_balance = get_account_balance(self.client)
after_sell_qty = get_samsung_holding_quantity(after_sell_balance)
logger.info(f"Samsung quantity after sell order: {after_sell_qty}")
```

## 7.8 로그 기록

본 시스템은 주요 실행 과정을 로그로 기록한다.

기록되는 내용은 다음과 같다.

- 토큰 재사용 또는 새 토큰 발급
- 현재가 조회 결과
- 주문 전 보유수량
- 매수 주문 요청
- 매도 주문 요청
- 주문 응답
- 주문 후 보유수량
- API 에러
- retry 시도
- 다음 사이클 대기 시간
- 거래 종료 시점

예시:

```
2026-06-10 15:25:44,761 | INFO | Current price for 005930: 303000
2026-06-10 15:25:44,762 | INFO | Current price: 303000
2026-06-10 15:25:50,240 | INFO | Holdings count: 0
2026-06-10 15:25:50,240 | INFO | Account summary: [{'dnca_tot_amt': '10000000', 'nxdy_excc_amt': '10035849', 'prvs_rcdl_excc_amt': '10035849', 'cma_evlu_amt': '0', 'bfdy_buy_amt': '6151000', 'thdt_buy_amt': '0', 'nxdy_auto_rdpt_amt': '0', 'bfdy_sll_amt': '6201000', 'thdt_sll_amt': '0', 'd2_auto_rdpt_amt': '0', 'bfdy_tlex_amt': '14151', 'thdt_tlex_amt': '0', 'tot_loan_amt': '0', 'scts_evlu_amt': '0', 'tot_evlu_amt': '10035849', 'nass_amt': '10035849', 'fncg_gld_auto_rdpt_yn': '', 'pchs_amt_smtl_amt': '0', 'evlu_amt_smtl_amt': '0', 'evlu_pfls_smtl_amt': '0', 'tot_stln_slng_chgs': '0', 'bfdy_tot_asst_evlu_amt': '10035849', 'asst_icdc_amt': '0', 'asst_icdc_erng_rt': '0.00000000'}]
2026-06-10 15:25:50,241 | INFO | Samsung quantity before order: 0
2026-06-10 15:25:55,200 | INFO | Pending Samsung orders count: 0
2026-06-10 15:25:55,201 | INFO | Adjusted buy price: 302000
2026-06-10 15:25:55,202 | INFO | Adjusted sell price: 304000
2026-06-10 15:25:55,202 | INFO | No Samsung shares. Submit buy order only.
2026-06-10 15:25:55,202 | INFO | Buy order request | stock=005930, price=302000, qty=1
2026-06-10 15:25:56,114 | INFO | Buy order response: {'rt_cd': '0', 'msg_cd': '40600000', 'msg1': '모의투자 매수주문이 완료 되었습니다.', 'output': {'KRX_FWDG_ORD_ORGNO': '00950', 'ODNO': '0000038614', 'ORD_TMD': '152556'}}
2026-06-10 15:25:56,114 | INFO | Buy order response: {'rt_cd': '0', 'msg_cd': '40600000', 'msg1': '모의투자 매수주문이 완료 되었습니다.', 'output': {'KRX_FWDG_ORD_ORGNO': '00950', 'ODNO': '0000038614', 'ORD_TMD': '152556'}}
2026-06-10 15:25:56,114 | INFO | Buy order submitted successfully.
2026-06-10 15:26:31,571 | INFO | Holdings count: 0
2026-06-10 15:26:31,572 | INFO | Account summary: [{'dnca_tot_amt': '10000000', 'nxdy_excc_amt': '10035849', 'prvs_rcdl_excc_amt': '10035849', 'cma_evlu_amt': '0', 'bfdy_buy_amt': '6151000', 'thdt_buy_amt': '0', 'nxdy_auto_rdpt_amt': '0', 'bfdy_sll_amt': '6201000', 'thdt_sll_amt': '0', 'd2_auto_rdpt_amt': '0', 'bfdy_tlex_amt': '14151', 'thdt_tlex_amt': '0', 'tot_loan_amt': '0', 'scts_evlu_amt': '0', 'tot_evlu_amt': '10035849', 'nass_amt': '10035849', 'fncg_gld_auto_rdpt_yn': '', 'pchs_amt_smtl_amt': '0', 'evlu_amt_smtl_amt': '0', 'evlu_pfls_smtl_amt': '0', 'tot_stln_slng_chgs': '0', 'bfdy_tot_asst_evlu_amt': '10035849', 'asst_icdc_amt': '0', 'asst_icdc_erng_rt': '0.00000000'}]
2026-06-10 15:26:31,572 | INFO | Samsung quantity after buy order: 0
2026-06-10 15:26:31,573 | INFO | Waiting 600 seconds before next cycle.
2026-06-10 15:36:31,573 | INFO | Trading window ended. Auto trader stopped.

```

---

# 8. How to Run

## 1. Repository Clone

```bash
git clone https://github.com/ksm12030-sudo/Korea-Investment-Auto-Trading-System.git
cd Korea-Investment-Auto-Trading-System 
(만약 파일이 내부 폴더에 있다면)
cd Korea-Investment-Auto-Trading-System (한번 더) 
```

## 2. 패키지 설치

```bash
pip install -r requirements.txt
```

## 3. `.env` 파일 생성

프로젝트 폴더 안에 `.env` 파일을 생성한다.

```
GH_APPKEY=your_app_key
GH_APPSECRET=your_app_secret
GH_ACCOUNT_NO=your_account_number
GH_ACCOUNT_PRODUCT_CODE=01
```

## 4. 프로그램 실행

```bash
python main.py
```

## 5. 예상 실행 흐름

거래시간 내에 실행하면 다음과 같은 로그가 출력된다.

```
Reusing cached access token
Auto trader started.
Current price for 005930: 317250
Current price: 317250
```

거래시간 전이면 대기하고, 15:30 이후에는 자동으로 종료된다.
