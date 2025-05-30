import yfinance as yf
import pandas as pd
import requests
from sqlalchemy import create_engine

# --- 1. Подключение к PostgreSQL ---
DB_URL = "postgresql+psycopg2://postgres:sultan2004@localhost/RASdevAI_auth"

engine = create_engine(DB_URL)

# --- 2. Получаем список акций S&P 500 ---
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]  # Берём первую таблицу
    return df["Symbol"].tolist()

tickers = get_sp500_tickers()
print(f"📊 Найдено {len(tickers)} тикеров: {tickers[:5]} ...")

# --- 3. Загружаем исторические данные ---
def download_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="10y")  # Данные за 10 лет
        if df.empty:
            return None
        df.reset_index(inplace=True)
        df["ticker"] = ticker  # Добавляем тикер в данные
        return df[["Date", "Open", "High", "Low", "Close", "Volume", "ticker"]]
    except Exception as e:
        print(f"❌ Ошибка загрузки {ticker}: {e}")
        return None
    
# --- 4. Сохраняем в PostgreSQL ---
def save_to_postgres(df, table_name="stock_prices"):
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"✅ Данные {df['ticker'][0]} сохранены в {table_name}")

last_ticker = "LII"
is_downloaded = True
# --- 5. Цикл по всем акциям ---
for ticker in tickers:
    if ticker == last_ticker:
        is_downloaded = False
    if is_downloaded:
        continue
    print(f"⏳ Загружаем {ticker} ...")
    df = download_stock_data(ticker)
    df.columns = df.columns.str.lower()
    if df is not None:
        save_to_postgres(df)

print("🎉 Готово! Все данные загружены.")



# CREATE TABLE stock_prices (
#     date DATE,
#     open FLOAT,
#     high FLOAT,
#     low FLOAT,
#     close FLOAT,
#     volume BIGINT,
#     ticker VARCHAR(10)
# );
