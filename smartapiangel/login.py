import os
import pyotp
import json
from dotenv import load_dotenv
from SmartApi import SmartConnect # Make sure this import is correct
from logzero import logger
# Remove Flask session import, it's not needed here anymore
# from flask import session

# Set the path for the angelweb directory
ANGELWEB_PATH = r"C:\Users\user\projects\angelweb"

def load_trading_env():
    """Loads the .env.trading environment file."""
    env_file = ".env.trading"
    env_path = os.path.join(ANGELWEB_PATH, env_file)
    if load_dotenv(env_path):
        logger.info(f"✅ {env_file} loaded successfully!")
    else:
        logger.error(f"❌ Failed to load {env_file}!")
    return env_file

# --- MODIFIED FUNCTION DEFINITION ---
def login(api_key, client_id, password, totp_secret):
    """
    Performs login using provided credentials and returns a result dictionary.
    """
    try:
        # load_trading_env() # Environment variables might not be needed if API key is passed directly

        # Use the arguments passed to the function
        API_KEY = api_key
        CLIENT_ID = client_id
        PASSWORD = password
        TOTP_SECRET = totp_secret

        if not all([API_KEY, CLIENT_ID, PASSWORD, TOTP_SECRET]):
            logger.error("Missing required login credentials passed to login function.")
            # Return error dictionary
            return {"status": False, "message": "Missing required login credentials."}

        totp = pyotp.TOTP(TOTP_SECRET).now() #generate totp using the secret
        smart_api = SmartConnect(api_key=API_KEY)
        logger.info(f"Attempting generateSession for client: {CLIENT_ID}")
        response = smart_api.generateSession(CLIENT_ID, PASSWORD, totp)
        logger.debug(f"generateSession response: {response}") # Log the raw response

        # Check response format and status
        if response and isinstance(response, dict) and response.get("status") == True:
            # Ensure 'data' key exists and contains necessary tokens
            if "data" in response and response["data"]:
                auth_token = response["data"].get("jwtToken")
                refresh_token = response["data"].get("refreshToken")
                feed_token = response["data"].get("feedToken")

                if not auth_token:
                     logger.error("Login successful but jwtToken missing in response data.")
                     return {"status": False, "message": "Login successful but jwtToken missing."}

                # Optional: Write token to file (Consider if this is still needed with session handling)
                token_path = os.path.join(ANGELWEB_PATH, "auth_token.json")
                try:
                    with open(token_path, "w") as file:
                        # Save more info if needed, or just the token
                        json.dump({"data": {"auth_token": auth_token, "client_id": CLIENT_ID}}, file)
                    logger.info(f"Auth token written to: {token_path}")
                except Exception as file_e:
                    logger.error(f"Failed to write auth token to file: {file_e}")

                logger.info("✅ Login Successful!")
                # Return success dictionary matching app.py expectation
                return {
                    "status": True,
                    "message": "Login Successful",
                    "data": {
                        "jwtToken": auth_token,
                        "refreshToken": refresh_token,
                        "feedToken": feed_token
                    }
                }
            else:
                logger.error("Login status True, but 'data' key missing or empty in response.")
                return {"status": False, "message": "Login successful but response data is missing."}
        else:
            # Handle failed login response
            error_msg = response.get("message", "Unknown login error") if isinstance(response, dict) else "Invalid response format from generateSession"
            logger.error(f"❌ Login Failed: {error_msg}")
            # Return error dictionary
            return {"status": False, "message": error_msg}

    except Exception as e:
        logger.exception(f"Exception during login process: {e}")
        # Return error dictionary for any exception
        return {"status": False, "message": f"Exception during login: {e}"}

# Remove or update the __main__ block as it won't work without credentials now
# if __name__ == "__main__":
#    print("This script needs to be called with credentials.")
#    # Example: result = login("YOUR_API_KEY", "YOUR_CLIENT_ID", "YOUR_PASS", "YOUR_TOTP_SECRET")
#    # print(result)
