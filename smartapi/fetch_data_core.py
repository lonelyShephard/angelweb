import json
from datetime import datetime
from smartapi.login import login
from logzero import logger
from flask import session
import os

# Set the path for the angelweb directory
ANGELWEB_PATH = r"C:\Users\user\projects\angelweb"

# Load stock symbols from stocks.json
def load_stocks(json_file):
    json_path = os.path.join(ANGELWEB_PATH, json_file)
    try:
        with open(json_path, "r") as file:
            data = json.load(file)
        return {entry["symbol"]: {"token": entry["token"], "exchange": entry["exchange"]} for entry in data}
    except Exception as e:
        print(f"❌ Error loading stocks: {e}")
        return {}

# Load stock data
stock_dict = load_stocks("stocks.json")

# Fetch LTP data
def fetch_ltp(exchange, symbol, token):
    smart_api, auth_token, refresh_token = login()
    if smart_api:
        try:
            stock_params = {
                "exchange": exchange,
                "tradingsymbol": symbol,
                "symboltoken": token
            }
            ltp_data = smart_api.ltpData(**stock_params)
            logger.info(f"LTP Data: {ltp_data}")
            return f"LTP: {ltp_data['data']['ltp']}"
        except Exception as e:
            logger.exception(f"Fetching LTP failed: {e}")
            return "Failed to fetch LTP data."

# Fetch Historical Data
def fetch_historical_data(symbol, token, exchange, interval, from_datetime, to_datetime, from_time, to_time):
    smart_api, auth_token, refresh_token = login()
    if smart_api is None:
        logger.error("Login Failed: Unable to login.")
        return "Unable to login."
    try:
        
        historic_params = {
            "exchange": exchange.strip(),
            "symboltoken": token.strip(),  # Token loaded from stocks.json
            "interval": interval.strip().upper(),
            "fromdate": from_datetime,
            "todate": to_datetime
        }
        logger.info(f"📡 Sending Historical Data Request: {historic_params}")
        
        # Use the auth token as is; the fallback branch has been removed.
        historical_data = smart_api.getCandleData(historic_params)
        logger.info(f"Historical Data: {historical_data}")
        return json.dumps(historical_data, indent=4)
        
    except Exception as e:
        logger.exception("Historical Data fetch failed: %s", e)
        return f"Failed to fetch historical data: {e}"
