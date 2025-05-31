import logging

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        # logging.FileHandler("logs/app.log"),
        logging.StreamHandler()  # выводит в консоль
    ]
)

logger = logging.getLogger("stock_service")
