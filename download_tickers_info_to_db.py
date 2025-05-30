import yfinance as yf
import pandas as pd
import requests
from sqlalchemy import create_engine
from urllib.parse import urlparse

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

# --- 3. Извлекаем информацию о компании через yfinance ---
def get_company_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            return None
        
        # Извлекаем домен из website для image_url
        website = info.get("website", "")
        domain = urlparse(website).netloc if website else ""
        image_url = f"https://logo.clearbit.com/{domain}" if domain else None

        # Собираем данные в словарь
        company_data = {
            "ticker": ticker,
            "shortName": info.get("shortName", ""),  # Краткое название компании
            "longName": info.get("longName", ""),    # Полное название компании
            "address": info.get("address1", ""),
            "city": info.get("city", ""),
            "country": info.get("country", ""),
            "website": website,
            "industry": info.get("industry", ""),
            "sector": info.get("sector", ""),
            "summary": info.get("longBusinessSummary", ""),
            "image_url": image_url
        }
        return company_data
    except Exception as e:
        print(f"❌ Ошибка получения информации для {ticker}: {e}")
        return None

# --- 4. Сохраняем данные в PostgreSQL ---
def save_to_postgres(df, table_name="company_info"):
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"✅ Данные сохранены в {table_name} для {len(df)} компаний")

# --- 5. Основной цикл обработки тикеров ---
def process_tickers(tickers):
    all_data = []
    for ticker in tickers:
        print(f"⏳ Обрабатываем {ticker} ...")
        company_info = get_company_info(ticker)
        if company_info:
            all_data.append(company_info)
    
    # Преобразуем список словарей в DataFrame
    if all_data:
        df = pd.DataFrame(all_data)
        df.columns = df.columns.str.lower()  # Приводим названия колонок к нижнему регистру
        save_to_postgres(df)
    else:
        print("⚠️ Нет данных для сохранения.")

# --- 6. Запуск обработки ---
process_tickers(tickers)
print("🎉 Готово! Все данные загружены.")


# CREATE TABLE company_info (
#     ticker VARCHAR(10) PRIMARY KEY,
#     shortname VARCHAR(100),          -- Краткое название компании
#     longname VARCHAR(255),           -- Полное название компании
#     address VARCHAR(255),
#     city VARCHAR(100),
#     country VARCHAR(100),
#     website VARCHAR(255),
#     industry VARCHAR(100),
#     sector VARCHAR(100),
#     summary TEXT,
#     image_url VARCHAR(255)
# );