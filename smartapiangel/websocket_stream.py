from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from logzero import logger
from . import config #changed this line
import os

def on_data(wsapp, message):
    logger.info(f"📈 Market Data: {message}")

def on_open(wsapp, sws):  # Pass sws as an argument
    logger.info("✅ WebSocket Connected!")
    sws.subscribe("abc123", 1, [{"exchangeType": 1, "tokens": ["26009"]}])

def on_error(wsapp, error):
    logger.error(f"WebSocket Error: {error}")

def on_close(wsapp):
    logger.info("❌ WebSocket Disconnected!")

def start_websocket():
    API_KEY = config.API_KEY
    CLIENT_ID = config.CLIENT_ID
    sws = SmartWebSocketV2(API_KEY, CLIENT_ID, "authToken", "feedToken")
    
    # Pass sws to on_open
    sws.on_open = lambda wsapp: on_open(wsapp, sws)
    sws.on_data = on_data
    sws.on_error = on_error
    sws.on_close = on_close

    sws.connect()
