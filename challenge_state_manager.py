import json
import os
from urllib.parse import urlparse, unquote
# WebsiteConnector is no longer directly used here as an import for type hinting in 'update'
# The actual connector instances will be passed in the 'connectors_map'

class ChallengeStateManager:
    def __init__(self, state_file_name='challenge_state.json', main_challenges_dir='../ctf'):
        # Note: state_file_name is just the name, not the full path yet.
        self.state_file_name = state_file_name
        self.challenges_directory = main_challenges_dir
        
        # self.state will be a dictionary: { "platform_key": [chal1, chal2], ... }
        self.state = self.load_state()
    
    def _get_full_state_file_path(self):
        """Helper to get the full path to the state file."""
        # The state file is global, so it's directly in challenges_directory
        return os.path.join(self.challenges_directory, self.state_file_name)

    def _get_platform_challenge_base_path(self, platform_key, category, challenge_name):
        """Constructs the base path for a specific challenge on a platform."""
        return os.path.join(self.challenges_directory, platform_key, category, challenge_name)

    def load_state(self):
        """
        Loads the state from the JSON file.
        The state is expected to be a dictionary mapping platform_keys to lists of challenges.
        """
        # Ensure the main challenges directory exists
        if not os.path.exists(self.challenges_directory):
            os.makedirs(self.challenges_directory, exist_ok=True)
            print(f"Created main challenges directory: {self.challenges_directory}")
        
        full_state_path = self._get_full_state_file_path()
        if os.path.exists(full_state_path):
            try:
                with open(full_state_path, 'r', encoding='utf-8') as f:
                    loaded_state = json.load(f)
                    # Basic validation for the new structure (must be a dict)
                    if not isinstance(loaded_state, dict):
                        print(f"Warning: State file at {full_state_path} is not in the expected dictionary format. Initializing empty state.")
                        return {}
                    return loaded_state
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from state file {full_state_path}: {e}. Initializing empty state.")
                return {}
            except Exception as e:
                print(f"Error opening state file {full_state_path}: {e}. Initializing empty state.")
                return {}
        return {} # Return empty dict if file doesn't exist
    
    def save_state(self):
        """Saves the current state (dictionary of platforms to challenge lists) to the JSON file."""
        full_state_path = self._get_full_state_file_path()
        try:
            with open(full_state_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving state file {full_state_path}: {e}")
            
    def get_challenge_from_state(self, platform_key, challenge_id):
        """
        Retrieves a specific challenge from the loaded state by platform and ID.
        """
        platform_challenges = self.state.get(platform_key, [])
        for chal in platform_challenges:
            if chal.get('id') == challenge_id:
                return chal
        return {} # Return empty dict if not found

    def is_pending(self, new_website_chal_data: dict):
        """
        Checks if a challenge (new_website_chal_data from website) needs an update
        compared to its state on disk.
        new_website_chal_data MUST contain 'platform' and 'id' keys.
        """
        platform_key = new_website_chal_data.get('platform')
        challenge_id = new_website_chal_data.get('id')

        if not platform_key or not challenge_id:
            print("Error: Challenge data missing 'platform' or 'id' for 'is_pending' check.")
            print(new_website_chal_data)
            return False # Cannot determine, assume not pending or handle as error
        
        old_data = self.get_challenge_from_state(platform_key, challenge_id)
        
        # If no old_data, it's definitely new/pending
        if not old_data:
            return True
        
        # If pending is true, return immediatly
        if old_data['pending']:
            return True
        
        # Fields to check for changes
        fields_to_compare = ['value', 'solves', 'solved_by_me']
        for field in fields_to_compare:
            if new_website_chal_data.get(field) != old_data.get(field):
                return True # Pending if any field differs
        
        return False # Not pending if all checked fields are the same
    
    @staticmethod # This can be a static method as it doesn't rely on instance state
    def get_filename_from_url(url: str):
        try:
            path = urlparse(url).path
            filename = os.path.basename(path)
            return unquote(filename) # Decode URL-encoded characters like %20
        except Exception:
            # fallback if URL is malformed or unexpected
            return "unknown_file"

    def update(self, all_challenges: list, connectors_map: dict, selected_category_filter: str):
        """
        Updates the local state and files for challenges.

        Args:
            all_challenges (list): A list of all challenge dictionaries fetched
                                                 from all websites. Each dict MUST have a 'platform' key.
            connectors_map (dict): A map of {platform_key: connector_instance}.
            selected_category_filter (str): A string like "platform_key/category_name" or "" for all,
                                            or None to update nothing.
        """
        if selected_category_filter is None: # User chose to update nothing
            print("No category selected for update. Skipping challenge processing.")
            return

        next_global_state = {} # We will build the new state here

        # Ensure all platforms from current websites have an entry in next_global_state
        for chal_data_from_web in all_challenges:
            platform_key = chal_data_from_web['platform']
            if platform_key not in next_global_state:
                next_global_state[platform_key] = []
        
        # Also, carry over platforms that might be in old state but not in current website fetch,
        # unless we decide to prune them. For now, let's start fresh with platforms seen in this run.
        # To keep old platforms if no challenges were fetched for them this run:
        # for p_key in self.state:
        #     if p_key not in next_global_state:
        #         next_global_state[p_key] = list(self.state[p_key]) # copy old state for that platform


        for chal_data_from_web in all_challenges:
            platform_key = chal_data_from_web['platform']
            challenge_id = chal_data_from_web['id']
            category_name = chal_data_from_web.get('category', 'dunno')
            challenge_name = chal_data_from_web.get('name', f"challenge_{challenge_id}")

            # Normalize challenge_name to be filesystem-friendly (basic example)
            safe_challenge_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in challenge_name).strip()
            if not safe_challenge_name: safe_challenge_name = f"challenge_{challenge_id}"


            current_platform_category_key = f"{platform_key}/{category_name}"
            
            # Determine if this specific challenge should be processed
            should_process_this_challenge = False
            if chal_data_from_web.get('pending', False): # 'pending' is pre-set by main.py
                if not selected_category_filter: # Empty string means update all pending
                    should_process_this_challenge = True
                elif current_platform_category_key == selected_category_filter:
                    should_process_this_challenge = True
            
            if should_process_this_challenge:
                print(f"\nProcessing update for: [{platform_key}] {safe_challenge_name} (Category: {category_name})")
                
                connector = connectors_map.get(platform_key)
                if not connector:
                    print(f"\tWarning: No active connector found for platform '{platform_key}'. Skipping API calls for this challenge.")
                    # Add the challenge as is, or based on old state, but cannot fetch new details
                    current_state_for_chal = self.get_challenge_from_state(platform_key, challenge_id)
                    if current_state_for_chal:
                         next_global_state[platform_key].append(current_state_for_chal)
                    else:
                        chal_data_from_web['pending'] = True # Still pending as we couldn't process
                        next_global_state[platform_key].append(chal_data_from_web)
                    continue

                # Define paths, now platform-aware
                challenge_base_fs_path = self._get_platform_challenge_base_path(platform_key, category_name, safe_challenge_name)
                challenge_files_subfolder_path = os.path.join(challenge_base_fs_path, 'challenge') # For attachments

                # Create directories
                # exist_ok=True means it won't raise an error if the directory already exists
                newly_created_challenge_files_subfolder = False
                if not os.path.exists(challenge_files_subfolder_path):
                    os.makedirs(challenge_files_subfolder_path, exist_ok=True)
                    print(f"\tCreated directory: {challenge_files_subfolder_path}")
                    newly_created_challenge_files_subfolder = True # Download files if this dir is new
                else:
                    # If you want to re-download files if some are missing, add logic here
                    pass


                print(f"\tFetching detailed info for '{safe_challenge_name}' from '{platform_key}'...")
                # Use the specific connector for this platform
                detailed_chal_data, solvers_list = connector.get_challenge_details(challenge_id)
                
                if not detailed_chal_data: # Solvers_list can be empty, but data is crucial
                    print(f"\tWarning: Failed to fetch detailed info for '{safe_challenge_name}'. It might be partially updated or skipped.")
                    # Add the web data (which is less detailed) and mark as still pending if needed
                    chal_data_from_web['pending'] = True # Failed to get details, so still pending
                    next_global_state[platform_key].append(chal_data_from_web)
                    continue
                
                # Update files based on detailed_chal_data
                # 1. general_info.md
                md_path = os.path.join(challenge_base_fs_path, 'general_info.md')
                print(f"\tWriting '{md_path}'")
                try:
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(f"# ({detailed_chal_data.get('id', challenge_id)}) {detailed_chal_data.get('name', challenge_name)}\n")
                        f.write(f"- Platform: {platform_key}\n")
                        f.write(f"- Category: {detailed_chal_data.get('category', category_name)}\n")
                        f.write(f"- {detailed_chal_data.get('value', 'N/A')} points\n")
                        solved_status = 'Solved' if detailed_chal_data.get('solved_by_me') else 'Not Solved'
                        f.write(f"- Status: {solved_status}\n\n")
                        f.write(f"## Description:\n{detailed_chal_data.get('description', 'No description provided.')}")
                except Exception as e:
                    print(f"\tError writing general_info.md for {safe_challenge_name}: {e}")

                # 2. solvers.txt
                solvers_path = os.path.join(challenge_base_fs_path, 'solvers.txt')
                print(f"\tWriting '{solvers_path}'")
                try:
                    with open(solvers_path, 'w', encoding='utf-8') as f:
                        f.write(f"{detailed_chal_data.get('solves', 0)} people solved this:\n")
                        for solver_name in solvers_list: # solvers_list should be a list of names
                            f.write(f"\t- {solver_name}\n")
                except Exception as e:
                    print(f"\tError writing solvers.txt for {safe_challenge_name}: {e}")
                        
                # 3. Download attachments
                # Logic: Download if the 'challenge' subfolder was just created,
                # OR if you implement a more sophisticated check (e.g., file missing, force update)
                if detailed_chal_data.get('files') and newly_created_challenge_files_subfolder:
                    print(f"\tDownloading attachments for '{safe_challenge_name}'...")
                    for file_relative_url in detailed_chal_data['files']: # Assuming 'files' is a list of relative URLs
                        attachment_name = ChallengeStateManager.get_filename_from_url(file_relative_url)
                        if not attachment_name or attachment_name == "unknown_file": # Skip if filename is problematic
                             print(f"\t\tCould not determine filename from URL: {file_relative_url}. Skipping.")
                             continue

                        print(f"\t\tDownloading '{attachment_name}'...")
                        file_content = connector.download_attachment(file_relative_url)
                        
                        if file_content is not None:
                            attachment_save_path = os.path.join(challenge_files_subfolder_path, attachment_name)
                            try:
                                with open(attachment_save_path, 'wb') as f:                        
                                    f.write(file_content)
                                print(f"\t\tSaved '{attachment_name}' to '{attachment_save_path}'")
                            except Exception as e:
                                print(f"\t\tError saving file {attachment_name}: {e}")
                        else:
                            print(f"\t\tFailed to download '{attachment_name}'.")
                
                # This challenge has been processed, update its state for saving
                # Use detailed_chal_data as it's more complete, but ensure 'platform' is there
                final_chal_data_for_state = dict(detailed_chal_data) # Make a copy
                final_chal_data_for_state['platform'] = platform_key 
                final_chal_data_for_state['pending'] = False # No longer pending
                next_global_state[platform_key].append(final_chal_data_for_state)

            else: # Challenge was not selected for processing or wasn't pending
                # Add its current state (or web state if no prior state) to the new state for this platform
                old_state_for_this_chal = self.get_challenge_from_state(platform_key, challenge_id)
                if old_state_for_this_chal:
                    # Ensure 'pending' status from web fetch is preserved if it's more current
                    # but only if it was truly pending from web, otherwise keep old 'pending' status
                    if 'pending' in chal_data_from_web and chal_data_from_web['pending']:
                         old_state_for_this_chal['pending'] = True
                    # else, if chal_data_from_web['pending'] is False, it means it's not pending from web,
                    # so old_state_for_this_chal['pending'] (which should also be False or absent) is fine.
                    next_global_state[platform_key].append(old_state_for_this_chal)
                else:
                    # If no old state, add the data from web (which might be marked as pending or not)
                    next_global_state[platform_key].append(chal_data_from_web)
        
        self.state = next_global_state # Replace the entire state with the newly built one