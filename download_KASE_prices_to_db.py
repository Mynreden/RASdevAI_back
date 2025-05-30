import requests
from sqlalchemy import create_engine
from datetime import datetime
import pandas as pd
import time
import random


tickers = ['AIRA', 'CCBN', 'KCEL', 'KEGC', 'KMGZ', 'KZAP',
       'KZTK', 'KZTO', 'FRHC_KZ', 'HSBKd', 'KSPId', 'KZAPd', 'IFDR',
       'KASE', 'KMGD', 'KZTKp', 'MMGZp', 'RAHT', 'AMGZp', 'ASBN', 'BAST',
       'BSUL', 'CCBNp', 'GB_ALTN', 'TSBNp', 'AKZM', 'CSEC', 'UTMKp',
       'AIRAd', 'KZTKd', 'MATN', 'INBNp', 'ULBS', 'ALMS', 'NRBNp6',
       'SABR', 'AKRL', 'TPIB', 'LZGR', 'MNZH', 'BENK', 'EKTN', 'ASLF',
       'ADLA', 'AMAN', 'KZHR', 'SATC', 'TMLZ', 'AZNO', 'TSBN', 'ATEC',
       'FFIN', 'SKSL', 'NRBN', 'UTMK', 'ANSA', 'SRBT', 'MREK', 'KATR',
       'RGBR', 'KOZN', 'SATCp', 'RGBRp', 'SHZN', 'KZIK', 'SAS_', 'KSNF',
       'SHUK', 'AZNOp', 'MMGZ', 'LNPT', 'KATRp', 'ASTL', 'KZCR', 'AAFD',
       'ADRP', 'AKGR', 'ALTV', 'AMXP', 'ASKQ', 'ASKQp', 'CRMG', 'EXCS',
       'EXCSp', 'EXPA', 'FHRP', 'JRES', 'KMCP', 'KY_TPL_', 'KZAZ',
       'KZCRp', 'LOGC', 'MKBW', 'PHYS', 'PZVA', 'SABRp', 'SHUKp', 'SHUP',
       'ZHLT']

base_url = "https://kase.kz/tv-charts/securities/history"
params = {
    "resolution": "1D",
    "from": 1262304000,  # 1 января 2010
    "to": 1742428800,   # 31 марта 2025
    "chart_language_code": "ru"
}


DB_URL = "postgresql+psycopg2://postgres:sultan2004@localhost/RASdevAI_auth"

engine = create_engine(DB_URL)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

session = requests.Session()
proxies = {
    "http": "socks4://213.74.223.69:4153",
    "https": "socks4://213.74.223.69:4153"
}

def fetch_and_save_stock_data(ticker):
    params["symbol"] = f"ALL:{ticker}"
    response = session.get(base_url, params=params, headers=headers)

    
    if response.status_code == 200:
        print(response.text)
        time.sleep(random.uniform(1, 5))  # Задержка от 1 до 5 секунд
        data = response.json()
        if data.get("s") == "ok":
            times = data["t"]
            opens = data["o"]
            highs = data["h"]
            lows = data["l"]
            closes = data["c"]
            volumes = data["v"]
            dates = map(lambda x: datetime.fromtimestamp(x).date(), times)
            df = pd.DataFrame({
                "date": dates,
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
                "ticker": [ticker] * len(times)
            })

            df.to_sql("stock_prices_kase", engine, if_exists="append", index=False)

            print(f"Данные для {ticker} успешно сохранены.")
        else:
            print(f"Ошибка для {ticker}: {data.get('s')}")
    else:
        print(f"Не удалось получить данные для {ticker}: {response.status_code}")

for ticker in tickers:
    fetch_and_save_stock_data(ticker)

print("Все данные сохранены в таблицу stock_prices.")

# CREATE TABLE IF NOT EXISTS stock_prices_kase (
#         date DATE,
#         open FLOAT,
#         high FLOAT,
#         low FLOAT,
#         close FLOAT,
#         volume BIGINT,
#         ticker VARCHAR(10)
#     );