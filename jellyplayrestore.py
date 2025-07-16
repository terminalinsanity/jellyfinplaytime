# jellyplayrestore.py

import requests
import json
import os
import logging
import sys

# --- Configuration ---
# Set your Jellyfin server URL, API Key, and backup file path here.
# If you set a specific value (e.g., "http://192.168.1.14:8096"), the script will use it directly.
# If you set it to None or an empty string, the script will prompt you for input at runtime.
JELLYFIN_URL = "" 	# Set to your URL, or leave blank for prompt
JELLYFIN_API = "" 	# Set to your API key, or leave blank for prompt
BACKUP_FILE = "" 	# Set to your desired output file, or leave blank for prompt

# --- Logging Setup ---
# Determine log file name dynamically based on the script's name
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
LOG_FILE = f"{SCRIPT_NAME}.log"

# Configure logging to file (INFO level by default for general use)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO, # Set to logging.DEBUG for very detailed request/response logs in the file
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add a console handler to also print logs to the console
# This means only WARNING, ERROR, and CRITICAL messages will appear in the console.
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING) # Set to WARNING to minimize console output
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# --- User Input Functions ---

def get_api_key_from_user():
    """Prompts the user for the Jellyfin API key without a default value."""
    api_key = input(f"Enter your Jellyfin API Key: ")
    return api_key.strip()

def get_jellyfin_url_from_user(default_url_for_prompt):
    """Prompts the user for the Jellyfin server URL, showing only the default."""
    jellyfin_url = input(f"Enter your Jellyfin Server URL (default: {default_url_for_prompt}): ")
    return jellyfin_url.strip() if jellyfin_url else default_url_for_prompt.strip()

def get_output_file_from_user(default_file_for_prompt):
    """Prompts the user for the backup JSON file name."""
    output_file = input(f"Enter the name for the JSON backup file (default: {default_file_for_prompt}): ")
    return output_file.strip() if output_file else default_file_for_prompt.strip()

# --- API Helper Functions ---

def make_api_request(method, url, api_key, params=None):
    """
    Helper function for making API requests to the Jellyfin server.
    Includes detailed logging for debugging.
    """
    headers = {
        "X-Emby-Token": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    logger.debug(f"DEBUG: Request Method: {method}")
    logger.debug(f"DEBUG: Request URL: {url}")
    logger.debug(f"DEBUG: Request Headers (intended): {headers}")
    if params:
        logger.debug(f"DEBUG: Request Params: {params}")

    response = None # Initialize response outside try block
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"API {method} Error on {url}: {e}")
        if response is not None:
            logger.error(f"Response Status Code: {response.status_code}")
            logger.error(f"Response Body: {response.text}") # Crucial for error details
            if hasattr(response, 'request') and hasattr(response.request, 'headers'):
                logger.error(f"Headers *actually sent* by requests: {response.request.headers}") # Crucial to see what went out
        return None

def get_all_users(jellyfin_url, api_key):
    """Fetches all users from the Jellyfin server."""
    logger.info("Fetching users...")
    print("Fetching users...") # Kept for immediate user feedback
    users_url = f"{jellyfin_url}/Users"
    response = make_api_request('GET', users_url, api_key)
    if response:
        return response.json()
    else:
        logger.error(f"Could not retrieve users from Jellyfin server.")
        print(f"Error retrieving users from Jellyfin server. Check log for details.") # Kept for immediate user feedback
        return None

def get_played_items_for_user(jellyfin_url, api_key, user_id):
    """Fetches all played items for a specific user."""
    logger.info(f"  Fetching played items for user ID: {user_id}...")
    print(f"  Fetching played items for user ID: {user_id}...") # Kept for immediate user feedback
    items_url = f"{jellyfin_url}/Users/{user_id}/Items"
    params = {
        "IsPlayed": "true",
        "Recursive": "true",
        "Fields": "UserData,RunTimeTicks,ProviderIds", # Ensure ProviderIds is requested
        "SortBy": "DatePlayed",
        "SortOrder": "Descending",
        "Limit": 10000 # Increase limit if you have a very large library
    }
    response = make_api_request('GET', items_url, api_key, params=params)
    if response:
        return response.json().get("Items", [])
    else:
        logger.error(f"  Error fetching played items for user {user_id}. Check log for details.")
        print(f"  Error fetching played items for user {user_id}. Check log for details.") # Kept for immediate user feedback
        return []

def main():
    logger.info("--- Jellyfin Playtime Backup Script Started ---")
    print("--- Jellyfin Playtime Backup Script ---") # Kept for initial banner

    # Determine Jellyfin URL
    if JELLYFIN_URL is None or JELLYFIN_URL == "":
        jellyfin_url = get_jellyfin_url_from_user("http://localhost:8096")
    else:
        jellyfin_url = JELLYFIN_URL

    # Determine API Key
    if JELLYFIN_API is None or JELLYFIN_API == "":
        api_key = get_api_key_from_user() # No default passed here
    else:
        api_key = JELLYFIN_API

    # Determine Output File Path
    if BACKUP_FILE is None or BACKUP_FILE == "":
        output_file_path = get_output_file_from_user("jellyplaytime.json")
    else:
        output_file_path = BACKUP_FILE

    # Log the configuration being used
    logger.info(f"Using Jellyfin URL: {jellyfin_url}")
    logger.info(f"Using API Key: {'*' * len(api_key)}") # Mask API key in logs for security
    logger.info(f"Using Output File: {output_file_path}")

    users = get_all_users(jellyfin_url, api_key)
    if not users:
        logger.error("No users found or error retrieving users. Exiting.")
        print("No users found or error retrieving users. Exiting.") # Kept for immediate user feedback
        return

    json_output_data = []

    for user in users:
        user_id = user.get("Id")
        username = user.get("Name")
        if not user_id or not username:
            logger.warning(f"Skipping user with incomplete data: {user}")
            print(f"Skipping user with incomplete data: {user}") # Kept for immediate user feedback
            continue

        logger.info(f"Processing user: {username} (ID: {user_id})")
        print(f"Processing user: {username} (ID: {user_id})") # Kept for immediate user feedback
        played_items = get_played_items_for_user(jellyfin_url, api_key, user_id)

        for item in played_items:
            item_id = item.get("Id")
            item_name = item.get("Name")
            item_type = item.get("Type")
            user_data = item.get("UserData", {})
            provider_ids = item.get("ProviderIds", {}) # Get the ProviderIds dictionary

            # Extract relevant fields from UserData
            playback_position_ticks = user_data.get("PlaybackPositionTicks", 0)
            play_count = user_data.get("PlayCount", 0)
            is_favorite = user_data.get("IsFavorite", False)
            played = user_data.get("Played", False)
            last_played_date = user_data.get("LastPlayedDate") # This is a string from API

            # Get external IDs from ProviderIds
            imdb_id = provider_ids.get("Imdb") # Key for IMDB ID is typically "Imdb"
            tmdb_id = provider_ids.get("Tmdb") # Key for TMDB ID is typically "Tmdb"
            tvdb_id = provider_ids.get("Tvdb") # Key for TVDB ID is typically "Tvdb"

            # Construct the dictionary for this item's playtime data
            item_playtime_data = {
                "UserId": user_id,
                "Username": username,
                "ItemId": item_id,
                "ItemName": item_name,
                "ItemType": item_type,
                "PlayCount": play_count,
                "PlaybackPositionTicks": playback_position_ticks,
                "IsFavorite": is_favorite,
                "Played": played,
                "LastPlayedDate": last_played_date, # Keep as string for JSON output
                "ImdbId": imdb_id, # Add IMDB ID
                "TmdbId": tmdb_id, # Add TMDB ID
                "TvdbId": tvdb_id  # Add TVDB ID
            }
            json_output_data.append(item_playtime_data)
            logger.debug(f"  Added '{item_name}' for {username} to backup data.")

    # Write to JSON file
    try:
        with open(output_file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_output_data, jsonfile, indent=2, ensure_ascii=False)
        logger.info(f"Successfully exported playtime data to {output_file_path}")
        print(f"\nSuccessfully exported playtime data to {output_file_path}") # Kept for final summary
    except IOError as e:
        logger.error(f"Error writing to JSON file: {e}")
        print(f"Error writing to JSON file: {e}") # Kept for immediate user feedback

    logger.info("--- Jellyfin Playtime Backup Script Finished ---")
    print("\nBackup script finished. Check the log file for details.") # Kept for final message

if __name__ == "__main__":
    main()