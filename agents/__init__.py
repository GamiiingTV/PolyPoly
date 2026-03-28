# Imports à la demande pour éviter les conflits de dépendances optionnelles
def get_market_scanner():
    from .market_scanner import MarketScanner
    return MarketScanner

def get_sentiment_agent():
    from .sentiment_agent import SentimentAgent
    return SentimentAgent

def get_prediction_agent():
    from .prediction_agent import PredictionAgent
    return PredictionAgent

def get_trading_agent():
    from .trading_agent import TradingAgent
    return TradingAgent

def get_learning_agent():
    from .learning_agent import LearningAgent
    return LearningAgent
