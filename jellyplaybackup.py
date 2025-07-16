# jellyplaybackup.py

import requests
import json
import os
import logging
import sys
from datetime import datetime

# --- Configuration ---
# Set your Jellyfin server URL, API Key, and backup file path here.
# If you set a specific value (e.g., "http://192.168.1.100:8096"), the script will use it directly.
# If you set it to None, the script will prompt you for input at runtime, offering a generic default.
JELLYFIN_URL = "" 	# Set to your URL, or leave blank for prompt
JELLYFIN_API = "" 	# Set to your API key, or leave blank for prompt
BACKUP_FILE = "" 	# Set to your desired output file, or leave blank for prompt


# --- API Headers ---
# These are base headers. The API key will be added dynamically.
BASE_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

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

# --- User Input Functions (Conditionally used) ---

def get_api_key_from_user(default_key_for_prompt):
    """Prompts the user for the Jellyfin API key."""
    api_key = input(f"Enter your Jellyfin API Key: ")
    return api_key.strip() if api_key else default_key_for_prompt.strip()

def get_jellyfin_url_from_user(default_url_for_prompt):
    """Prompts the user for the Jellyfin server URL."""
    jellyfin_url = input(f"Enter your Jellyfin Server URL (default: {default_url_for_prompt}): ")
    return jellyfin_url.strip() if jellyfin_url else default_url_for_prompt.strip()

def get_backup_file_from_user(default_file_for_prompt):
    """Prompts the user for the backup JSON file path."""
    backup_file = input(f"Enter the path to your JSON backup file (default: {default_file_for_prompt}): ")
    return backup_file.strip() if backup_file else default_file_for_prompt.strip()

# --- API Helper Functions ---

def make_api_request(method, url, api_key, params=None, json_data=None):
    """
    Helper function for making API requests to the Jellyfin server.
    Includes detailed logging for debugging.
    """
    headers = BASE_HEADERS.copy()
    headers["X-Emby-Token"] = api_key # The correct header for your setup

    logger.debug(f"DEBUG: Request Method: {method}")
    logger.debug(f"DEBUG: Request URL: {url}")
    logger.debug(f"DEBUG: Request Headers (intended): {headers}")
    if params:
        logger.debug(f"DEBUG: Request Params: {params}")
    if json_data:
        logger.debug(f"DEBUG: Request Body (intended): {json.dumps(json_data, indent=2)}")

    response = None # Initialize response outside try block
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=json_data, timeout=10)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"API {method} Error on {url}: {e}")
        if response is not None:
            logger.error(f"Response Status Code: {response.status_code}")
            logger.error(f"Response Body: {response.text}") # Crucial for error details
            if hasattr(response, 'request') and hasattr(response.request, 'headers'):
                logger.error(f"Headers *actually sent* by requests: {response.request.headers}") # Crucial to see what went out
        return None

# --- Core Logic Functions ---

def load_backup_data(file_path):
    """Loads the JSON backup data from the specified file path."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded backup data from {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"Error: Backup file not found at '{file_path}'. Please check the path.")
        print(f"Error: Backup file not found at '{file_path}'. Please check the path.") # Kept for immediate user feedback
        return None
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from '{file_path}'. Is it a valid JSON file?")
        print(f"Error: Could not decode JSON from '{file_path}'. Is it a valid JSON file?") # Kept for immediate user feedback
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading backup data: {e}")
        print(f"An unexpected error occurred while loading backup data: {e}") # Kept for immediate user feedback
        return None

def get_jellyfin_users(base_url, api_key):
    """Retrieves and returns a list of users from the target Jellyfin server."""
    users_url = f"{base_url}/Users"
    response = make_api_request('GET', users_url, api_key)
    if response:
        return response.json()
    else:
        logger.error(f"Could not retrieve users from current Jellyfin server.")
        print(f"Error retrieving users from target Jellyfin server. Check log for details.") # Kept for immediate user feedback
        return None

def select_user_from_list(user_list, prompt_text):
    """Prompts the user to select a user from a given list."""
    if not user_list:
        logger.warning("No users found to select from.")
        print("No users found to select from.") # Kept for immediate user feedback
        return None

    print(f"\n{prompt_text}") # Kept print for the main prompt
    for i, user in enumerate(user_list):
        print(f"{i + 1}. Name: {user.get('Name')}, ID: {user.get('Id')})") # Kept print for list display

    while True:
        try:
            choice = input("Enter the number of the desired user: ")
            index = int(choice) - 1
            if 0 <= index < len(user_list):
                selected_user = user_list[index]
                logger.info(f"Selected user: {selected_user.get('Name')} (ID: {selected_user.get('Id')})")
                return selected_user
            else:
                logger.warning("Invalid user selection. User entered: %s", choice)
                print("Invalid choice. Please enter a number within the range.") # Kept for immediate user feedback
        except ValueError:
            logger.warning("Invalid input for user selection (not a number). User entered: %s", choice)
            print("Invalid input. Please enter a number.") # Kept for immediate user feedback

def select_backup_user_from_data(backup_data):
    """Prompts the user to select a username from unique usernames in the backup data."""
    if not backup_data:
        logger.error("Backup data is empty or invalid.")
        print("Backup data is empty or invalid.") # Kept for immediate user feedback
        return None

    unique_usernames = sorted(list(set(entry['Username'] for entry in backup_data if entry.get("Username"))))
    if not unique_usernames:
        logger.error("No usernames found in the backup file.")
        print("No usernames found in the backup file.") # Kept for immediate user feedback
        return None

    print("\nSelect a user from the backup file to restore FROM:") # Kept print for the main prompt
    for i, username in enumerate(unique_usernames):
        print(f"{i + 1}. {username}") # Kept print for list display

    while True:
        try:
            choice = input("Enter the number of the desired backup user: ")
            index = int(choice) - 1
            if 0 <= index < len(unique_usernames):
                selected_username = unique_usernames[index]
                logger.info(f"Selected backup user: {selected_username}")
                return selected_username
            else:
                logger.warning("Invalid backup user selection. User entered: %s", choice)
                print("Invalid choice. Please enter a number within the range.") # Kept for immediate user feedback
        except ValueError:
            logger.warning("Invalid input for backup user selection (not a number). User entered: %s", choice)
            print("Invalid input. Please enter a number.") # Kept for immediate user feedback

def get_jellyfin_media_map(base_url, api_key):
    """
    Retrieves all movies and episodes from Jellyfin and creates a mapping
    from external IDs (IMDb, TMDB, TVDB) to Jellyfin internal IDs.
    This map is built once at the beginning for efficient lookups.
    """
    logger.info("Retrieving all media items from Jellyfin to build external ID map (this may take a moment for large libraries)...")
    print("Retrieving all media items from Jellyfin to build external ID map (this may take a moment for large libraries)...") # Kept for immediate user feedback
    
    jellyfin_id_map = {}
    params = {
        'recursive': 'true',
        'fields': 'ProviderIds', # Only ProviderIds are needed for mapping
        'includeItemTypes': 'Movie,Episode',
        'limit': 500, # Page size for fetching items
        'startIndex': 0
    }
    
    total_retrieved = 0
    page = 0

    while True:
        params['startIndex'] = page * params['limit']
        items_url = f"{base_url}/Items" # Use /Items for global library access
        response = make_api_request('GET', items_url, api_key, params=params)

        if not response:
            logger.error("Failed to retrieve media items from Jellyfin. Cannot build media map.")
            print("Failed to retrieve media items from Jellyfin. Cannot build media map.") # Kept for immediate user feedback
            break

        items_data = response.json()
        items = items_data.get('Items', [])
        
        if not items:
            logger.debug(f"No more items or empty response on page {page}.")
            break

        for item in items:
            item_id = item.get('Id')
            provider_ids = item.get('ProviderIds')
            
            if item_id and provider_ids:
                if 'Imdb' in provider_ids and provider_ids['Imdb']:
                    jellyfin_id_map[f"Imdb:{provider_ids['Imdb']}"] = item_id
                if 'Tmdb' in provider_ids and provider_ids['Tmdb']:
                    jellyfin_id_map[f"Tmdb:{provider_ids['Tmdb']}"] = item_id
                if 'Tvdb' in provider_ids and provider_ids['Tvdb']:
                    jellyfin_id_map[f"Tvdb:{provider_ids['Tvdb']}"] = item_id
            # else: logger.debug(f"Item '{item.get('Name')}' (ID: {item_id}) missing ID or ProviderIds.)"
        
        total_retrieved += len(items)
        total_record_count = items_data.get('TotalRecordCount', 0)
        
        # Log progress to file, but do NOT print to console for every 500 items
        logger.info(f"Retrieved {total_retrieved}/{total_record_count} media items for mapping (page {page}).")

        if total_retrieved >= total_record_count:
            break
        page += 1

    logger.info(f"Finished building external ID map. Mapped {len(jellyfin_id_map)} unique external IDs.")
    # print(f"Finished building external ID map. Mapped {len(jellyfin_id_map)} unique external IDs.") # Removed from console
    return jellyfin_id_map

def restore_playtime_data(base_url, api_key, target_user_id, backup_user_data, jellyfin_media_map):
    """
    Restores playtime data for a specific user using the pre-built media map.
    """
    restored_count = 0
    failed_count = 0

    logger.info(f"\n--- Starting Data Restoration for Target User ID: {target_user_id} ---")
    print(f"\n--- Starting Data Restoration for Target User ID: {target_user_id} ---") # Kept for immediate user feedback

    for item_data in backup_user_data:
        item_name = item_data.get("ItemName", "Unknown Item")
        item_id_backup = item_data.get("ItemId", "N/A") # This is the old ItemId from backup
        imdb_id = item_data.get("ImdbId")
        tmdb_id = item_data.get("TmdbId")
        tvdb_id = item_data.get("TvdbId")
        item_type = item_data.get("ItemType")

        logger.info(f"Processing backup item: '{item_name}' (Type: {item_type}, Backup Item ID: {item_id_backup})")
        # print(f"\n  Processing backup item: '{item_name}' (Type: {item_type}, Backup Item ID: {item_id_backup})") # Removed from console

        target_item_id = None
        # Look up in the pre-built map using prioritized external IDs
        if imdb_id:
            target_item_id = jellyfin_media_map.get(f"Imdb:{imdb_id}")
            if target_item_id:
                logger.info(f"Matched '{item_name}' using IMDb ID: {imdb_id}")
        if not target_item_id and tmdb_id:
            target_item_id = jellyfin_media_map.get(f"Tmdb:{tmdb_id}")
            if target_item_id:
                logger.info(f"Matched '{item_name}' using TMDB ID: {tmdb_id}")
        if not target_item_id and tvdb_id:
            target_item_id = jellyfin_media_map.get(f"Tvdb:{tvdb_id}")
            if target_item_id:
                logger.info(f"Matched '{item_name}' using TVDB ID: {tvdb_id}")

        if not target_item_id:
            log_message = (f"Skipping '{item_name}' (Backup Item ID: {item_id_backup}). "
                           f"No matching item found in current Jellyfin library using IMDB: {imdb_id}, "
                           f"TMDB: {tmdb_id}, TVDB: {tvdb_id}.")
            logger.warning(log_message)
            print(f"    {log_message}") # Kept for immediate user feedback on skipped items
            failed_count += 1
            continue

        logger.info(f"Found matching item on target server. New Item ID: {target_item_id}")
        # print(f"    Found matching item on target server. New Item ID: {target_item_id}") # Removed from console

        # Step 2: Prepare the UserData payload for restoration
        payload = {
            "PlaybackPositionTicks": item_data.get("PlaybackPositionTicks", 0),
            "PlayCount": item_data.get("PlayCount", 0),
            "IsFavorite": item_data.get("IsFavorite", False),
            "Played": item_data.get("Played", False),
        }
        # LastPlayedDate needs to be handled carefully. Jellyfin might expect ISO format.
        # Pass it only if it exists in backup, otherwise omit.
        if 'LastPlayedDate' in item_data and item_data['LastPlayedDate'] is not None:
            payload['LastPlayedDate'] = item_data['LastPlayedDate']

        # Step 3: Send the POST request to update UserData
        update_url = f"{base_url}/Users/{target_user_id}/Items/{target_item_id}/UserData"
        
        response = make_api_request('POST', update_url, api_key, json_data=payload)
        if response:
            logger.info(f"Successfully updated playtime for '{item_name}'.")
            # print(f"    Successfully updated playtime for '{item_name}'.") # Removed from console
            restored_count += 1
        else:
            # Error is already logged by make_api_request
            failed_count += 1
    
    logger.info(f"\n--- Restoration Summary ---")
    logger.info(f"Successfully restored {restored_count} items.")
    logger.info(f"Failed to restore {failed_count} items.")
    logger.info(f"---------------------------")
    # Keep final summary prints for console
    print(f"\n--- Restoration Summary ---")
    print(f"Successfully restored {restored_count} items.")
    print(f"Failed to restore {failed_count} items.")
    print("---------------------------")


def main():
    logger.info("--- Jellyfin Playtime Restoration Script Started ---")
    print("--- Jellyfin Playtime Restoration Script ---") # Kept for initial banner

    # Determine Jellyfin URL
    if JELLYFIN_URL is None or JELLYFIN_URL == "":
        jellyfin_url = get_jellyfin_url_from_user("http://localhost:8096")
    else:
        jellyfin_url = JELLYFIN_URL

    # Determine API Key
    if JELLYFIN_API is None or JELLYFIN_API == "":
        api_key = get_api_key_from_user("")
    else:
        api_key = JELLYFIN_API

    # Determine Backup File Path
    if BACKUP_FILE is None or BACKUP_FILE == "":
        backup_file_path = get_backup_file_from_user("jellyplaytime.json")
    else:
        backup_file_path = BACKUP_FILE

    # Log the configuration being used
    logger.info(f"Using Jellyfin URL: {jellyfin_url}")
    logger.info(f"Using API Key: {'*' * len(api_key)}") # Mask API key in logs for security
    logger.info(f"Using Backup File: {backup_file_path}")

    backup_data = load_backup_data(backup_file_path)
    if not backup_data:
        logger.error("No backup data loaded. Exiting script.")
        print("No backup data loaded. Exiting script.") # Kept for immediate user feedback
        return

    # Phase 1: User Mapping
    target_users = get_jellyfin_users(jellyfin_url, api_key)
    if not target_users:
        logger.error("Cannot proceed without target Jellyfin users.")
        print("Cannot proceed without target Jellyfin users. Exiting script.") # Kept for immediate user feedback
        return

    selected_target_user = select_user_from_list(target_users, "Select a user from the current Jellyfin server to restore TO:")
    if not selected_target_user:
        logger.error("No target user selected. Exiting script.")
        print("No target user selected. Exiting script.") # Kept for immediate user feedback
        return
    target_user_id = selected_target_user.get("Id")

    selected_backup_username = select_backup_user_from_data(backup_data)
    if not selected_backup_username:
        logger.error("No backup user selected. Exiting script.")
        print("No backup user selected. Exiting script.") # Kept for immediate user feedback
        return

    # Filter backup data for the selected username
    backup_user_data = [item for item in backup_data if item.get("Username") == selected_backup_username]
    if not backup_user_data:
        logger.warning(f"No playtime data found for '{selected_backup_username}' in the backup file. Exiting script.")
        print(f"No playtime data found for '{selected_backup_username}' in the backup file. Exiting.") # Kept for immediate user feedback
        return

    # Phase 2: Build Global Media Map
    jellyfin_media_map = get_jellyfin_media_map(jellyfin_url, api_key)
    if not jellyfin_media_map:
        logger.error("Could not build Jellyfin media map. Cannot proceed with restoration.")
        print("Could not build Jellyfin media map. Cannot proceed with restoration.") # Kept for immediate user feedback
        return

    # Phase 3: Item Lookup and Data Restoration
    restore_playtime_data(jellyfin_url, api_key, target_user_id, backup_user_data, jellyfin_media_map)

    logger.info("--- Jellyfin Playtime Restoration Script Finished ---")
    print("\nRestoration script finished. Check the log file for details.") # Kept for final message

if __name__ == "__main__":
    main()