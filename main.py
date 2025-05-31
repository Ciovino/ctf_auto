import os
import configparser
import importlib # For dynamically importing modules
from collections import defaultdict

from challenge_state_manager import ChallengeStateManager

def get_pending_categories(state_manager: ChallengeStateManager, all_challenges: list[dict]):
    pending_categories = defaultdict(int)
    
    for chal in all_challenges:
        platform = chal.get('platform', 'unknown_platform')
        category = chal.get('category', 'dunno')
        platform_category_key = f"{platform}/{category}"
        
        chal['pending'] = state_manager.is_pending(chal)
        if chal['pending']:
            pending_categories[platform_category_key] += 1
            
    return pending_categories

def prompt_for_category_selection(categories_with_counts: dict):
    if not categories_with_counts:
        print('All challenges are up to date across all platforms.')
        return None
    
    print('\nChoose which platform/category to update:')
    print("0. Update all pending challenges")
    
    # Create a list of the category keys to maintain order for selection
    category_keys_list = list(categories_with_counts.keys())
    
    for idx, platform_category_key in enumerate(category_keys_list, start=1):
        num_pending = categories_with_counts[platform_category_key]
        print(f'{idx}. {platform_category_key} ({num_pending} pending)')
        
    try:
        user_choice = int(input('> ').strip())
    except ValueError:
        print('Invalid input. Updating nothing.')
        return None
    
    if user_choice == 0:
        print('Updating all pending challenges...')
        return "" # "" (empty string) signifies all categories
    elif 1 <= user_choice <= len(category_keys_list):
        selected_key = category_keys_list[user_choice - 1]
        print(f'Updating challenges in {selected_key}...')
        return selected_key # Returns the specific platform/category key
    else:
        print('Invalid selection. Updating nothing.')
        return None

def dynamically_import_connector(class_path_string: str):
    try:
        module_path, class_name = class_path_string.rsplit('.', 1)
        module = importlib.import_module(module_path)
        connector_class = getattr(module, class_name)
        return connector_class
    except (ImportError, AttributeError, ValueError) as e:
        print(f"Error importing connector class '{class_path_string}': {e}")
        return None

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    caller_cwd = os.getcwd()
    config_file_path = os.path.join(script_dir, 'config.ini')

    try:
        os.chdir(script_dir)
        print(f'Current working directory: {os.getcwd()}')
        
        if not os.path.exists(config_file_path):
            print(f"'{config_file_path}' not found.")
            print("Please create a config.ini file with your site configurations.")
            print('Check out the "config.ini.example"')
            exit(1)

        config = configparser.ConfigParser()
        config.read(config_file_path)

        default_main_challenges_dir = '../ctf' # Default if not in config
        default_state_file_name = 'challenge_state.json' # Default if not in config

        if 'global_settings' in config:
            main_challenges_dir_from_config = config.get('global_settings', 'main_challenges_dir', fallback=default_main_challenges_dir)
            state_file_name_from_config = config.get('global_settings', 'state_file_name', fallback=default_state_file_name)
            print(f"Global settings loaded: Main directory='{main_challenges_dir_from_config}', State file='{state_file_name_from_config}'")
        else:
            main_challenges_dir_from_config = default_main_challenges_dir
            state_file_name_from_config = default_state_file_name
            print(f"No [global_settings] section found. Using defaults: Main directory='{main_challenges_dir_from_config}', State file='{state_file_name_from_config}'")

        all_challenges_from_all_platforms = []
        active_connectors = {} 
        
        # Pass the loaded global settings to ChallengeStateManager
        state_manager = ChallengeStateManager(
            main_challenges_dir=main_challenges_dir_from_config,
            state_file_name=state_file_name_from_config
        )

        print("\nProcessing configured CTF platforms...")
        for platform_key in config.sections():
            if platform_key == 'global_settings': # Skip the global_settings section
                continue
            
            print(f"\n--- Platform: {platform_key} ---")
            if not config.getboolean(platform_key, 'enabled', fallback=False):
                print(f"Platform '{platform_key}' is disabled. Skipping.")
                continue

            base_url = config.get(platform_key, 'base_url', fallback=None)
            username = config.get(platform_key, 'username', fallback=None)
            password = config.get(platform_key, 'password', fallback=None)
            connector_class_str = config.get(platform_key, 'connector', fallback=None)

            if not all([base_url, connector_class_str]):
                print(f"Missing 'base_url' or 'connector' for '{platform_key}'. Skipping.")
                continue
            
            ConnectorClass = dynamically_import_connector(connector_class_str)
            if not ConnectorClass:
                print(f"Could not load connector for '{platform_key}'. Skipping.")
                continue

            # Instantiate connector
            connector_instance = ConnectorClass(base_url, username, password)
            
            print(f"Attempting login to '{platform_key}'...")
            if connector_instance.login():
                print(f"Successfully logged into '{platform_key}'.")
                active_connectors[platform_key] = connector_instance
                
                print(f"Fetching challenges from '{platform_key}'...")
                platform_challenges = connector_instance.get_challenges()
                
                if platform_challenges is not None:
                    # Tag challenges with their platform
                    for chal in platform_challenges:
                        chal['platform'] = platform_key 
                    all_challenges_from_all_platforms.extend(platform_challenges)
                    print(f"Fetched {len(platform_challenges)} challenges from '{platform_key}'.")
                else:
                    print(f"Failed to fetch challenges from '{platform_key}'.")
            else:
                print(f"Login failed for '{platform_key}'.")
        
        if not all_challenges_from_all_platforms:
            print("\nNo challenges fetched from any platform. Exiting.")
            exit(0)
            
        print("\n--- Challenge Status Summary ---")
        pending_platform_categories = get_pending_categories(state_manager, all_challenges_from_all_platforms)
        selected_platform_category_key = prompt_for_category_selection(pending_platform_categories)
        
        if selected_platform_category_key is not None: # If None, user chose to update nothing
            print(f"\n--- Updating Challenges ({selected_platform_category_key if selected_platform_category_key else 'All Pending'}) ---")
            state_manager.update(
                all_challenges=all_challenges_from_all_platforms, 
                connectors_map=active_connectors, # Pass the map of active connectors
                selected_category_filter=selected_platform_category_key
            )
        
        print("\nSaving current challenge state...")
        state_manager.save_state()
        print("Challenge state saved.")

    except FileNotFoundError:
        print(f"Error: config.ini not found at {config_file_path}. Please create it.")
    except configparser.Error as e:
        print(f"Error reading or parsing config.ini: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        os.chdir(caller_cwd)
        print(f'\nRestored working directory to: {os.getcwd()}')