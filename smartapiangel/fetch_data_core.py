# c:\Users\user\projects\angelweb\smartapiangel\fetch_data_core.py
import json
from datetime import datetime
# REMOVE: from smartapiangel.login import login
from logzero import logger
# REMOVE: from flask import session # Core logic should not depend on Flask session
import os
from SmartApi import SmartConnect # Import for type hinting

# Set the path for the angelweb directory
ANGELWEB_PATH = r"C:\Users\user\projects\angelweb"

# Load stock symbols from stocks.json
def load_stocks(json_file):
    json_path = os.path.join(ANGELWEB_PATH, json_file)
    try:
        with open(json_path, "r") as file:
            data = json.load(file)
        # Ensure data is a list of dictionaries as expected
        if isinstance(data, list):
             return {entry["symbol"]: {"token": entry["token"], "exchange": entry["exchange"]} for entry in data if isinstance(entry, dict) and "symbol" in entry and "token" in entry and "exchange" in entry}
        else:
            logger.error(f"❌ Error loading stocks: {json_file} does not contain a list of stock entries.")
            return {}
    except FileNotFoundError:
        logger.error(f"❌ Error loading stocks: File not found at {json_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"❌ Error loading stocks: Could not decode JSON from {json_path}")
        return {}
    except Exception as e:
        logger.exception(f"❌ Error loading stocks: {e}")
        return {}

# Load stock data
stock_dict = load_stocks("stocks.json")
if not stock_dict:
    logger.warning("Stock dictionary is empty. Ensure stocks.json is present and correctly formatted.")


# Fetch LTP data - MODIFIED
def fetch_ltp(smart_api: SmartConnect, exchange, symbol, token):
    # REMOVE: smart_api, auth_token, refresh_token = login() # Removed internal login call
    if smart_api: # Check if a valid object was passed
        try:
            stock_params = {
                "exchange": exchange,
                "tradingsymbol": symbol,
                "symboltoken": token
            }
            ltp_data = smart_api.ltpData(**stock_params)
            logger.info(f"LTP Data Response: {ltp_data}")
            # More robust checking
            if ltp_data and ltp_data.get("status") and ltp_data.get("data") and "ltp" in ltp_data["data"]:
                 logger.info(f"LTP for {symbol}: {ltp_data['data']['ltp']}")
                 return f"LTP: {ltp_data['data']['ltp']}"
            else:
                 error_msg = ltp_data.get("message", "Unknown error") if isinstance(ltp_data, dict) else "Invalid response"
                 logger.error(f"LTP data fetch failed or malformed for {symbol}: {error_msg} | Full Response: {ltp_data}")
                 return f"Failed to fetch LTP data ({error_msg})."
        except Exception as e:
            logger.exception(f"Fetching LTP failed for {symbol}: {e}")
            return f"Failed to fetch LTP data (Exception: {e})."
    else:
        logger.error("fetch_ltp called without a valid smart_api object.")
        return "Failed to fetch LTP data (no API connection)."


# Fetch Historical Data - MODIFIED
def fetch_historical_data(smart_api: SmartConnect, symbol, token, exchange, interval, from_datetime, to_datetime):
    # REMOVE: smart_api, auth_token, refresh_token = login() # Removed internal login call
    if smart_api is None: # Check if a valid object was passed
        logger.error("fetch_historical_data called without a valid smart_api object.")
        return json.dumps({"status": False, "message": "Unable to fetch data (no API connection)."}, indent=4)

    try:
        historic_params = {
            "exchange": exchange.strip(),
            "symboltoken": token.strip(),
            "interval": interval.strip().upper(),
            "fromdate": from_datetime, # Ensure these are strings 'YYYY-MM-DD HH:MM'
            "todate": to_datetime   # Ensure these are strings 'YYYY-MM-DD HH:MM'
        }
        logger.info(f"📡 Sending Historical Data Request: {historic_params}")

        # Use the passed smart_api object
        historical_data = smart_api.getCandleData(historic_params)
        logger.info(f"Historical Data Raw Response for {symbol}: {historical_data}") # Log raw response

        # Add more robust checking
        if historical_data and isinstance(historical_data, dict):
            if historical_data.get("status") == True and "data" in historical_data:
                logger.info(f"Historical Data Fetched Successfully for {symbol}.")
                # Return the actual data structure, let the caller handle JSON dumping if needed elsewhere
                return historical_data
            elif historical_data.get("status") == False:
                error_msg = historical_data.get('message', 'Unknown error')
                logger.error(f"Historical Data fetch failed for {symbol}: {error_msg}")
                return {"status": False, "message": f"Failed to fetch historical data: {error_msg}", "details": historical_data}
            else:
                logger.error(f"Historical Data fetch failed for {symbol} with unexpected response format: {historical_data}")
                return {"status": False, "message": "Failed to fetch historical data: Unexpected response format.", "details": historical_data}
        else:
             logger.error(f"Historical Data fetch received invalid response type for {symbol}: {type(historical_data)}")
             return {"status": False, "message": "Failed to fetch historical data: Invalid response type from API.", "details": str(historical_data)}


    except Exception as e:
        logger.exception(f"Historical Data fetch failed for {symbol}: {e}")
        return {"status": False, "message": f"Failed to fetch historical data: {e}"}

