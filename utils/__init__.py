from .database import Database
from .polymarket_api import GammaAPI, CLOBClient, parse_market

# TelegramNotifier importé à la demande pour éviter les conflits de dépendances
def get_telegram_notifier():
    from .telegram_bot import TelegramNotifier
    return TelegramNotifier
