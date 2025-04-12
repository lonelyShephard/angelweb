# c:\Users\user\projects\angelweb\smartapiangel\exit_smartapi.py
import os
import json
# REMOVE: from dotenv import load_dotenv # No longer loading env here
from SmartApi import SmartConnect
from logzero import logger

# Set the path for the angelweb directory (still needed for potential logging/config if used elsewhere)
ANGELWEB_PATH = r"C:\Users\user\projects\angelweb"

# REMOVE: load_trading_env function
# REMOVE: load_auth_data function

# This function remains mostly the same, just used by the modified logout below
def attempt_logout(smart_api: SmartConnect, client_id, description):
    """Attempts logout using the provided SmartConnect object and client ID."""
    if not smart_api or not client_id:
        logger.error(f"Logout attempt failed: Missing SmartConnect object or Client ID for {description}.")
        return {"status": False, "message": "Missing API object or Client ID for logout."}
    try:
        logger.info(f"Attempting terminateSession for client: {client_id} ({description})")
        response = smart_api.terminateSession(client_id)
        if response and isinstance(response, dict) and response.get("status") == True:
            logger.info(f"Logout Successful via API ({description})! Response: {response}")
        else:
            error_msg = response.get("message", "Unknown error") if isinstance(response, dict) else "Invalid response"
            logger.error(f"Logout Failed via API ({description})! Message: {error_msg} | Response: {response}")
        return response # Return the full response
    except Exception as e:
        logger.exception(f"Exception during terminateSession call ({description}): {e}")
        return {"status": False, "message": f"Exception during API logout: {e}"}


# Logout function - MODIFIED to accept parameters
def logout(auth_token, client_id, api_key):
    """
    Logs out the user session using the provided credentials.
    Should be called from the Flask app's logout route.
    """
    if not all([auth_token, client_id, api_key]):
        logger.error("Logout function called with missing parameters (auth_token, client_id, or api_key).")
        return {"status": False, "message": "Logout requires token, client ID, and API key."}

    try:
        # Create a SmartConnect instance specifically for logout
        # Provide API key to SmartConnect so that X-PrivateKey header is set.
        smart_api = SmartConnect(api_key=api_key)

        # Set the access token obtained during login (passed from Flask session)
        # Remove "Bearer " prefix if present (though generateSession usually doesn't include it)
        if auth_token.startswith("Bearer "):
            auth_token = auth_token[len("Bearer "):]
        smart_api.setAccessToken(auth_token) # Crucial step

        # Attempt logout using the initialized object
        logout_response = attempt_logout(smart_api, client_id, "Flask Session Logout")
        return logout_response

    except Exception as e:
        logger.exception(f"Error during logout process setup: {e}")
        return {"status": False, "message": f"Logout error: {e}"}

# REMOVE or comment out the __main__ block as it won't work correctly anymore
# if __name__ == "__main__":
#     print("This script should be called with auth_token, client_id, api_key")
#     # Example: logout("your_token", "your_client_id", "your_api_key")

