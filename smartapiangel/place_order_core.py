# c:\Users\user\projects\angelweb\smartapiangel\place_order_core.py
import json
import time
# REMOVE: from smartapiangel.login import login
from logzero import logger
# REMOVE: from flask import session # Core logic should not depend on Flask session
import os
from SmartApi import SmartConnect # Import for type hinting

# Set the path for the angelweb directory
ANGELWEB_PATH = r"C:\Users\user\projects\angelweb"

# Load stock symbols from stocks.json. (Copied from fetch_data_core, ensure consistency or centralize)
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


# Place order function - MODIFIED
def place_order(smart_api: SmartConnect, tradingsymbol, symboltoken, transactiontype, exchange, ordertype, producttype, quantity, price):
    # REMOVE: smart_api, auth_token, refresh_token = login() # Removed internal login call

    if smart_api: # Check if a valid object was passed
        try:
            # Basic validation (can be enhanced)
            if not all([tradingsymbol, symboltoken, transactiontype, exchange, ordertype, producttype, quantity]):
                logger.error("Missing required order parameters.")
                return {"status": False, "message": "Missing required order parameters."}
            if ordertype == "LIMIT" and not price:
                 logger.error("Price is required for LIMIT orders.")
                 return {"status": False, "message": "Price is required for LIMIT orders."}
            if ordertype == "MARKET":
                price = "0" # Market orders typically use 0 for price

            # Define order parameters
            order_params = {
                "variety": "NORMAL", # Could be parameterised if needed (AMO, ROBO etc)
                "tradingsymbol": str(tradingsymbol),
                "symboltoken": str(symboltoken),
                "transactiontype": str(transactiontype).upper(), # BUY/SELL
                "exchange": str(exchange).upper(), # NSE/BSE/NFO etc.
                "ordertype": str(ordertype).upper(), # MARKET/LIMIT/STOPLOSS_LIMIT/STOPLOSS_MARKET
                "producttype": str(producttype).upper(), # DELIVERY/INTRADAY/MARGIN/CARRYFORWARD/COVER/BRACKET
                "duration": "DAY", # Or IOC
                "price": str(price), # Use 0 for Market order
                "squareoff": "0", # For Cover/Bracket orders
                "stoploss": "0", # For Stoploss orders / Cover/Bracket
                "quantity": str(quantity)
            }
            logger.info(f"Attempting to place order with params: {order_params}")

            # Place order using the passed smart_api object
            order_response = smart_api.placeOrder(order_params)
            logger.info(f"Place Order Raw Response: {order_response}")

            # Check response structure and content
            if order_response and isinstance(order_response, dict):
                if order_response.get("status") == True and order_response.get("data") and "orderid" in order_response["data"]:
                    order_id = order_response["data"]["orderid"]
                    logger.info(f"✅ Order Placed Successfully! Order ID: {order_id}")
                    # Optionally check status immediately (consider if needed, might be too soon)
                    # check_order_status(smart_api, order_id, delay=0)
                    return {"status": True, "message": f"Order placed successfully. Order ID: {order_id}", "order_id": order_id}
                else:
                    error_msg = order_response.get("message", "Unknown error")
                    logger.error(f"❌ Order placement failed by API: {error_msg} | Full Response: {order_response}")
                    return {"status": False, "message": f"Order placement failed: {error_msg}", "details": order_response}
            else:
                 logger.error(f"❌ Order placement failed: Invalid response format received. Response: {order_response}")
                 return {"status": False, "message": "Order placement failed: Invalid response format.", "details": str(order_response)}


        except Exception as e:
            logger.exception(f"❌ Order placement failed with exception: {e}")
            return {"status": False, "message": f"Order placement failed: {e}"}
    else:
        logger.error("place_order called without a valid smart_api object.")
        return {"status": False, "message": "Order placement failed (no API connection)."}


# Function to check order status - MODIFIED (accepts smart_api)
def check_order_status(smart_api: SmartConnect, order_id):
    if not smart_api:
        logger.error("check_order_status called without valid smart_api object.")
        return {"status": False, "message": "Cannot check status (no API connection)."}
    if not order_id:
        logger.error("check_order_status called without order_id.")
        return {"status": False, "message": "Order ID required to check status."}

    try:
        logger.info(f"Checking status for Order ID: {order_id}")
        order_book = smart_api.orderBook()
        logger.debug(f"Order Book Response: {order_book}")

        if order_book and isinstance(order_book, dict) and order_book.get("status") == True:
            if order_book.get("data"):
                for order in order_book["data"]:
                    if order.get("orderid") == str(order_id): # Ensure comparison is correct type
                        status = order.get('status', 'N/A')
                        logger.info(f"Status for Order {order_id}: {status}")
                        return {"status": True, "order_status": status, "order_details": order}
                logger.warning(f"⚠️ Order {order_id} not found in the order book data.")
                return {"status": False, "message": f"Order {order_id} not found in order book."}
            else:
                logger.info(f"Order book data is empty or null for Order ID {order_id}.")
                # This might be valid if no orders exist, treat as not found for specific ID
                return {"status": False, "message": f"Order {order_id} not found (empty order book data)."}
        else:
            error_msg = order_book.get("message", "Unknown error") if isinstance(order_book, dict) else "Invalid response"
            logger.error(f"❌ Failed to fetch order book: {error_msg} | Full Response: {order_book}")
            return {"status": False, "message": f"Failed to fetch order book: {error_msg}", "details": order_book}

    except Exception as e:
        logger.exception(f"❌ Error fetching order status for {order_id}: {e}")
        return {"status": False, "message": f"Error fetching order status: {e}"}

