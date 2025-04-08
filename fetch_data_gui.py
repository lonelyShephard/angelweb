import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from login import login
from logzero import logger

# Load stock symbols from stocks.json
def load_stocks(json_file):
    try:
        with open(json_file, "r") as file:
            data = json.load(file)
        return {entry["symbol"]: {"token": entry["token"], "exchange": entry["exchange"]} for entry in data}
    except Exception as e:
        print(f"❌ Error loading stocks: {e}")
        return {}

# Fetch LTP data
def fetch_ltp():
    smart_api, auth_token, refresh_token = login()
    if smart_api:
        try:
            stock_params = {
                "exchange": exchange_var.get(),
                "tradingsymbol": symbol_var.get(),
                "symboltoken": token_var.get()
            }
            ltp_data = smart_api.ltpData(**stock_params)
            logger.info(f"LTP Data: {ltp_data}")
            ltp_result.set(f"LTP: {ltp_data['data']['ltp']}")
        except Exception as e:
            logger.exception(f"Fetching LTP failed: {e}")
            messagebox.showerror("Error", "Failed to fetch LTP data.")

# Fetch Historical Data
def fetch_historical_data():
    smart_api, auth_token, refresh_token = login()
    if smart_api is None:
        messagebox.showerror("Login Failed", "Unable to login.")
        return
    try:
        # Get date portions from the DateEntry widgets.
        date_from = from_date_entry.get_date()
        date_to   = to_date_entry.get_date()
        
        # Always use the spinboxes for time input.
        from_hour = from_hour_spin.get().zfill(2)
        from_min  = from_minute_spin.get().zfill(2)
        to_hour   = to_hour_spin.get().zfill(2)
        to_min    = to_minute_spin.get().zfill(2)
        
        # Build complete datetime strings using the provided time inputs.
        from_date_str = date_from.strftime("%Y-%m-%d") + f" {from_hour}:{from_min}"
        to_date_str   = date_to.strftime("%Y-%m-%d")   + f" {to_hour}:{to_min}"
        
        # Debug prints for verification.
        print(f"Final fromdate: {from_date_str}")
        print(f"Final todate: {to_date_str}")
        
        historic_params = {
            "exchange": exchange_var.get().strip(),
            "symboltoken": token_var.get().strip(),  # Token loaded from stocks.json
            "interval": interval_var.get().strip().upper(),
            "fromdate": from_date_str,
            "todate": to_date_str
        }
        logger.info(f"📡 Sending Historical Data Request: {historic_params}")
        
        # Use the auth token as is; the fallback branch has been removed.
        historical_data = smart_api.getCandleData(historic_params)
        logger.info(f"Historical Data: {historical_data}")
        history_result.set(json.dumps(historical_data, indent=4))
        
    except Exception as e:
        logger.exception("Historical Data fetch failed: %s", e)
        messagebox.showerror("Error", f"Failed to fetch historical data: {e}")

# Update stock token & exchange fields when symbol is selected
def update_stock_details(event=None):
    selected_symbol = symbol_var.get().upper()
    if (selected_symbol in stock_dict):
        token_var.set(stock_dict[selected_symbol]["token"])
        exchange_var.set(stock_dict[selected_symbol]["exchange"])
    else:
        token_var.set("")
        exchange_var.set("")

# Autocomplete function for stock symbol dropdown
def filter_symbols(event):
    typed_value = symbol_var.get().upper()
    matching_symbols = [s for s in stock_dict.keys() if typed_value in s]
    symbol_menu["values"] = matching_symbols

# Load stock data
stock_dict = load_stocks("stocks.json")

# GUI Setup
root = tk.Tk()
root.title("SmartAPI Data Fetcher")

# Stock Symbol Dropdown with Autocomplete
symbol_var = tk.StringVar()
ttk.Label(root, text="Stock Symbol:").pack()
symbol_menu = ttk.Combobox(root, textvariable=symbol_var, values=list(stock_dict.keys()))
symbol_menu.pack()
symbol_menu.bind("<KeyRelease>", filter_symbols)
symbol_menu.bind("<<ComboboxSelected>>", update_stock_details)

# Stock Token Field (Auto-filled)
token_var = tk.StringVar()
ttk.Label(root, text="Stock Token:").pack()
token_entry = ttk.Entry(root, textvariable=token_var, state="readonly")
token_entry.pack()

# Exchange Field (Auto-filled)
exchange_var = tk.StringVar()
ttk.Label(root, text="Exchange:").pack()
exchange_entry = ttk.Entry(root, textvariable=exchange_var, state="readonly")
exchange_entry.pack()

# Fetch LTP Button & Display
ltp_result = tk.StringVar()
ltp_label = ttk.Label(root, textvariable=ltp_result, font=("Arial", 10, "bold"))
ltp_label.pack()
fetch_ltp_button = ttk.Button(root, text="Fetch LTP", command=fetch_ltp)
fetch_ltp_button.pack()

# Interval Dropdown (Default: ONE_DAY)
interval_var = tk.StringVar(value="ONE_DAY")
ttk.Label(root, text="Interval:").pack()
interval_menu = ttk.Combobox(root, textvariable=interval_var, 
                             values=["ONE_MINUTE", "FIVE_MINUTE", "ONE_DAY"])
interval_menu.pack()

# **Dropdown Calendar for Date Selection**
ttk.Label(root, text="From Date:").pack()
from_date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
from_date_entry.pack()

ttk.Label(root, text="To Date:").pack()
to_date_entry = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
to_date_entry.pack()

# Time Entries for Non-DAY Interval
ttk.Label(root, text="From Time (HH:MM):").pack()
time_frame_from = ttk.Frame(root)
time_frame_from.pack()
from_hour_spin = ttk.Spinbox(time_frame_from, from_=0, to=23, width=3, format="%02.0f")
from_hour_spin.pack(side="left")
ttk.Label(time_frame_from, text=":").pack(side="left")
from_minute_spin = ttk.Spinbox(time_frame_from, from_=0, to=59, width=3, format="%02.0f")
from_minute_spin.pack(side="left")

ttk.Label(root, text="To Time (HH:MM):").pack()
time_frame_to = ttk.Frame(root)
time_frame_to.pack()
to_hour_spin = ttk.Spinbox(time_frame_to, from_=0, to=23, width=3, format="%02.0f")
to_hour_spin.pack(side="left")
ttk.Label(time_frame_to, text=":").pack(side="left")
to_minute_spin = ttk.Spinbox(time_frame_to, from_=0, to=59, width=3, format="%02.0f")
to_minute_spin.pack(side="left")

def update_time_defaults(event=None):
    interval = interval_var.get().strip().upper()
    if interval == "ONE_DAY":
        from_hour_spin.set("00")
        from_minute_spin.set("00")
        to_hour_spin.set("23")
        to_minute_spin.set("59")
    else:
        from_hour_spin.set("09")
        from_minute_spin.set("00")
        to_hour_spin.set("15")
        to_minute_spin.set("30")

# Bind the update function to the interval combobox selection change
interval_menu.bind("<<ComboboxSelected>>", update_time_defaults)

# Set defaults for initial state based on ONE_DAY
update_time_defaults()

# Fetch Historical Data Button & Display
history_result = tk.StringVar()
history_label = ttk.Label(root, textvariable=history_result, wraplength=500)
history_label.pack()
fetch_history_button = ttk.Button(root, text="Fetch Historical Data", command=fetch_historical_data)
fetch_history_button.pack()

# Run GUI
root.mainloop()

