import os
import json # Added for load_stocks
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
# Import necessary functions from your smartapi module
# Note: We are NOT importing 'place_order' anymore for the /trading route
from smartapi import login, fetch_historical_data, start_websocket, logout
from logzero import logger

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key

# Load default values from .env.trading
def load_default_env():
    default_env = {}
    try:
        with open(".env.trading", "r") as f:
            for line in f:
                # Added strip() to handle potential whitespace around key/value
                key, value = line.strip().split("=", 1)
                default_env[key.strip()] = value.strip()
        logger.info("Loaded default environment variables from .env.trading")
    except FileNotFoundError:
        logger.warning(".env.trading not found, using empty defaults.")
    except Exception as e:
        logger.error(f"Error loading .env.trading: {e}")
    return default_env

default_env = load_default_env()

# --- Load stocks for symbol->token/exchange lookup (similar to GUI) ---
# Needed for the revised /trading route, even if validation happens frontend
def load_stocks(json_file="stocks.json"):
    try:
        with open(json_file, "r") as file:
            data = json.load(file)
        # Create dictionary {symbol: {token, exchange}} - Ensure keys are uppercase
        stock_dict = {entry["symbol"].upper(): {"token": entry["token"], "exchange": entry["exchange"]} for entry in data}
        logger.info(f"Loaded {len(stock_dict)} stocks from {json_file}")
        return stock_dict
    except FileNotFoundError:
        logger.error(f"❌ Error: {json_file} not found.")
        return {}
    except Exception as e:
        logger.error(f"❌ Error loading stocks from {json_file}: {e}")
        return {}

stock_dict = load_stocks() # Load stocks globally

# --- Index / Login Route ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        api_key = request.form.get("api_key")
        client_id = request.form.get("client_id")
        password = request.form.get("password")
        totp_secret = request.form.get("totp_secret")

        # Store credentials in session - IMPORTANT for login() later
        session["api_key"] = api_key
        session["client_id"] = client_id
        session["password"] = password
        session["totp_secret"] = totp_secret
        session["logged_in"] = False # Assume not logged in until login() succeeds

        # Call login() - Ensure it reads from session if available
        smart_api, auth_token, refresh_token = login()
        if smart_api:
            session["logged_in"] = True
            logger.info("Login successful via web.")
            return redirect(url_for("dashboard"))
        else:
            logger.error("Login failed via web.")
            session.clear() # Clear session on failed login
            return render_template("index.html", error="Login failed!", default_env=default_env)

    # Clear session if accessing login page via GET while potentially logged in
    # session.clear() # Optional: uncomment to force re-login on visiting index
    return render_template("index.html", default_env=default_env)

# --- Dashboard Route ---
@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        logger.warning("Access denied to /dashboard: Not logged in.")
        return redirect(url_for("index"))
    return render_template("dashboard.html")

# --- REVISED Trading Route (Based on place_order_gui.py) ---
@app.route("/trading", methods=["GET", "POST"])
def trading():
    if not session.get("logged_in"):
        logger.warning("Access denied to /trading: Not logged in.")
        return redirect(url_for("index"))

    message = None
    error = None

    if request.method == "POST":
        # Call login() here to get a fresh smart_api object, using stored session credentials
        # Ensure your login() function in smartapi.py can use session data
        smart_api, _, _ = login()

        if not smart_api:
            error = "Failed to get API connection. Please log in again."
            logger.error("Trading action failed: Could not get smart_api object via login().")
            # Consider clearing session or redirecting to login
            # session.clear()
            # return redirect(url_for("index", error="Session expired or invalid, please login again."))
            return render_template("trading.html", error=error) # Stay on page with error

        try:
            # Get form data - Ensure frontend sends these names
            tradingsymbol = request.form.get("symbol", "").upper() # Use .get with default, ensure uppercase
            symboltoken = request.form.get("token", "")           # Get token from form (MUST be sent by frontend JS)
            exchange = request.form.get("exchange", "")         # Get exchange from form (MUST be sent by frontend JS)
            transactiontype = request.form.get("transaction")
            ordertype = request.form.get("order_type")
            producttype = request.form.get("product_type")
            quantity = request.form.get("quantity")
            price = request.form.get("price") or "0" # Default to "0" if empty (for MARKET orders)

            # --- Frontend Responsibility Reminder ---
            # CRITICAL: The frontend (trading.html + JS) MUST ensure that when a user selects
            # a 'symbol', the corresponding 'token' and 'exchange' are also populated
            # (e.g., in hidden inputs) and submitted with the form.

            # Basic validation (similar to GUI)
            if not all([tradingsymbol, symboltoken, exchange, transactiontype, ordertype, producttype, quantity]):
                error = "Missing required order parameters. Ensure symbol is valid (check token/exchange from frontend) and all fields are filled."
                logger.error(f"Order validation failed. Data received: {request.form}")
                return render_template("trading.html", error=error, **request.form) # Pass form data back

            # Construct the order_params dictionary EXACTLY like the GUI
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": tradingsymbol,
                "symboltoken": symboltoken,
                "transactiontype": transactiontype,
                "exchange": exchange,
                "ordertype": ordertype,
                "producttype": producttype,
                "duration": "DAY",
                "price": price,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": quantity
            }

            logger.info(f"Attempting to place order via web with params: {order_params}")

            # Call the placeOrder method directly on the smart_api object
            # This bypasses any potential issues in a separate smartapi.place_order wrapper
            order_id = smart_api.placeOrder(order_params)

            if order_id:
                # The API might return more details, check documentation if needed
                message = f"Order Placed Successfully! Order ID: {order_id}"
                logger.info(f"✅ Web order successful: {message}")
                # Optional: Add order status check here if needed, similar to GUI
                # status = check_order_status(smart_api, order_id) # If you implement this
                # message += f" | Status: {status}"
            else:
                # Check if placeOrder returns None/False or raises an exception on failure
                # This handles the case where it returns a non-exception falsy value
                error = "Order placement failed. API did not return an Order ID or indicated failure."
                logger.error(f"{error} Params: {order_params}")

        except Exception as e:
            error = f"Order placement failed: {e}"
            logger.exception(f"❌ Web order placement failed. Params: {request.form}")

        # Render the template with message or error, passing back form data helps refill form
        return render_template("trading.html", message=message, error=error, **request.form)

    # For GET request, just render the empty form
    return render_template("trading.html")


# --- Historical Data Route (Retained from original app.py) ---
@app.route("/historical", methods=["GET", "POST"])
def historical():
    if not session.get("logged_in"):
        logger.warning("Access denied to /historical: Not logged in.")
        return redirect(url_for("index"))

    message = None # Will hold the fetched data or error message
    form_data = request.form # Keep form data to refill form on POST

    if request.method == "POST":
        try:
            # Get form data
            symbol = form_data.get("symbol", "").upper() # Ensure uppercase
            token = form_data.get("token", "")          # MUST be sent by frontend JS
            exchange = form_data.get("exchange", "")    # MUST be sent by frontend JS
            interval = form_data.get("interval")
            from_date = form_data.get("from_date")
            to_date = form_data.get("to_date")
            from_hour = form_data.get("from_hour", "09") # Default times
            from_minute = form_data.get("from_minute", "15")
            to_hour = form_data.get("to_hour", "15")
            to_minute = form_data.get("to_minute", "30")

            # Basic validation
            if not all([symbol, token, exchange, interval, from_date, to_date]):
                 message = "Error: Missing required fields for historical data."
                 logger.error(f"Historical data validation failed. Data: {form_data}")
                 return render_template("historical.html", message=message, **form_data)

            # Format the dates and times as required by the SmartAPI
            # Example format: "YYYY-MM-DD HH:MM"
            from_datetime = f"{from_date} {from_hour}:{from_minute}"
            to_datetime = f"{to_date} {to_hour}:{to_minute}"

            logger.info(f"Fetching historical data for {symbol} ({token}/{exchange}) from {from_datetime} to {to_datetime}, interval {interval}")

            # Call fetch_historical_data (ensure this function handles login/auth internally)
            # Assuming fetch_historical_data takes these arguments in order
            result = fetch_historical_data(
                exchange=exchange,
                symboltoken=token,
                interval=interval,
                fromdate=from_datetime,
                todate=to_datetime
            )
            # Store the result (data or error message) to display in the template
            # Format result for display (e.g., pretty print JSON)
            if isinstance(result, (dict, list)):
                 message = json.dumps(result, indent=4)
                 logger.info("Successfully fetched historical data.")
            else:
                 message = f"Failed to fetch historical data: {result}" # Assuming result contains error string on failure
                 logger.error(message)

        except Exception as e:
            message = f"An error occurred while fetching historical data: {e}"
            logger.exception("Exception in /historical route:")
            # Render template with error message and retain form data
            return render_template("historical.html", message=message, **form_data)

    # Render the template, passing message and form data (for GET or after POST)
    return render_template("historical.html", message=message, **form_data)


# --- Streaming Route ---
@app.route("/streaming")
def streaming():
    if not session.get("logged_in"):
        logger.warning("Access denied to /streaming: Not logged in.")
        return redirect(url_for("index"))
    # Ensure start_websocket() uses session credentials or tokens correctly
    # start_websocket() # Call this appropriately based on your websocket implementation
    logger.info("Streaming page accessed (ensure websocket connection is handled correctly).")
    return render_template("streaming.html")

# --- Logout Route ---
@app.route("/logout")
def logout_route():
    if session.get("logged_in"):
        try:
            # Call the logout function from smartapi module (ensure it exists and works)
            logout()
            logger.info("User logged out via web (smartapi logout called).")
        except ImportError:
            logger.warning("smartapi.logout function not found, clearing session only.")
        except Exception as e:
            logger.error(f"Error during smartapi logout: {e}")
        finally:
            session.clear() # Always clear the session
            logger.info("Flask session cleared.")
            return redirect(url_for("index"))
    return redirect(url_for("index"))

# --- Static Files Route ---
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# --- Main Execution ---
if __name__ == "__main__":
    # Consider adding host='0.0.0.0' to make it accessible on your network
    # Use port other than default 5000 if needed, e.g., port=5001
    app.run(debug=True) #, host='0.0.0.0', port=5001)
