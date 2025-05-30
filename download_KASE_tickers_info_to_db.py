import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from urllib.parse import urlparse

# --- 1. Подключение к PostgreSQL ---
DB_URL = "postgresql+psycopg2://postgres:sultan2004@localhost/RASdevAI_auth"
engine = create_engine(DB_URL)

tickers =  ['CCBN', 'HSBK', 'KCEL', 'KEGC', 'KMGZ', 'KZAP',
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



# ['HSBKd', 'KSPId', 'KZAPd', 'IFDR',
#        'KZTKp', 'MMGZp', 'AMGZp', 'CCBNp', 'TSBNp', 'UTMKp',
#        'AIRAd', 'KZTKd', 'INBNp', 'NRBNp6',
#        'SATCp', 'RGBRp', 'AZNOp', 'KATRp', 'ASKQp',
#        'EXCSp', 'KZCRp', 'SABRp', 'SHUKp',]

# --- 2. Функция для парсинга HTML и извлечения данных о компании ---
def parse_company_info(html_content):
    try:
        # Парсим HTML с помощью BeautifulSoup
        # with open("page_dump.html", "w", encoding="utf-8") as f:
        #     f.write(html_content)
        soup = BeautifulSoup(html_content, "html.parser")
        if not soup:
            print("❌ парсинг не удался")
            return None
        soup = soup.find("div", class_="company")
        if not soup:
            print("❌ Блок 'div.company' не найден.")
            return None

        # Извлекаем данные из элемента
        ticker = soup.find("span").text.strip()  # "AIRA"
        if not ticker:
            print("❌ Блок 'ticker' не найден.")
            return None
        long_name = soup.find("h2").text.strip()  # "Air Astana JSC"
        if not long_name:
            print("❌ Блок 'long_name' не найден.")
            return None
        short_name = long_name.replace("JSC", "").strip()
        
        # Извлекаем строки с информацией (Phone, Address, Site и т.д.)
        info_rows = soup.find_all("div", class_="row")
        company_data = {"ticker": ticker, "shortname": short_name, "longname": long_name}
        
        for row in info_rows:
            
            label = row.find("div", class_="label").text.strip()
            value = row.find("div", class_="value")
            
            if label == "Address":
                full_address = value.text.strip()  # "Republic of Kazakhstan, 050039, Almaty, Turksibsky district, Zakarpatskaya st., 4A"
                # Разделяем адрес на город, страну и улицу
                address_parts = full_address.split(", ")
                company_data["country"] = address_parts[0]  # "Republic of Kazakhstan"
                company_data["city"] = address_parts[2]     # "Almaty"
                company_data["address"] = " ".join(address_parts[-2:]) # "Zakarpatskaya st., 4A"
            
            elif label == "Site":
                website = value.find("a")["href"]  # "https://airastana.com/"
                company_data["website"] = website.replace("https://", "")  # "airastana.com/"
                # Генерируем image_url на основе домена
                domain = urlparse(website).netloc
                company_data["image_url"] = f"https://logo.clearbit.com/{domain}"
            
            elif label == "Primary activity":
                company_data["summary"] = value.text.strip()  # Описание деятельности
            
            company_data["industry"] = ""
            company_data["sector"] = ""

        return company_data
    
    except Exception as e:
        print(f"❌ Ошибка парсинга HTML: {e}")
        return None

# --- 3. Сохраняем данные в PostgreSQL ---
def save_to_postgres(df, table_name="company_info"):
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"✅ Данные сохранены в {table_name} для {len(df)} компаний")

# --- 4. Основной цикл обработки HTML ---
all_data = []
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

session = requests.Session()

for ticker in tickers:
    page = session.get(f'https://kase.kz/en/listing/issuers/{ticker}', headers=headers).text
    print(f'⏳ Обрабатываем {ticker}...')
    company_info = parse_company_info(page)
    if company_info:
        all_data.append(company_info)

if all_data:
    df = pd.DataFrame(all_data)
    df.columns = df.columns.str.lower()  # Приводим названия колонок к нижнему регистру
    save_to_postgres(df)
    print(df.head())
else:
    print("⚠️ Нет данных для сохранения.")

print("🎉 Готово! Все данные загружены.")