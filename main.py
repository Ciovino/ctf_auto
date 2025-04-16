from website_connector import WebsiteConnector
from challenge_state_manager import ChallengeStateManager
from collections import defaultdict
import os

def get_pending_categories(state: ChallengeStateManager, challenges: list[dict]):
    pending_categories = defaultdict(int)
    
    for chal in challenges:
        category = chal.get('category', 'dunno')
        chal['pending'] = state.is_pending(chal)
        if chal['pending']:
            pending_categories[category] += 1
    
    return pending_categories

def prompt_for_category(categories):
    if len(categories) == 0:
        print('All up to date')
        return None
    
    print('Choose which category to update:')
    print("0. Update all")
    for idx, (cat, num_pending) in enumerate(categories.items(), start = 1):
        print(f'{idx}. {cat} ({num_pending} pending)')
        
    try:
        update = int(input('> ').strip())
    except ValueError:
        print('Not a valid input\nUpdating nothing')
        return None
    
    if update == 0:
        print('Updating all')
        return ''
    elif 1 <= update <= len(categories):
        selected = list(categories.keys())[update - 1]
        print(f'Updating {selected}')
        return selected
    else:
        print('Updating nothing')
        return None

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    caller_cwd = os.getcwd()
    
    try:
        os.chdir(script_dir)
        print(f'Changing to {os.getcwd()}')
    
        base_url = "https://cc-ctfd.m0lecon.it"
        connector = WebsiteConnector(base_url)
        state_manager = ChallengeStateManager()
        
        if connector.login():
            print("Logged in :)")
        else:
            print("Login failed :(")
            exit(-1)
            
        challenges = connector.get_challenges()
        pending_categories = get_pending_categories(state_manager, challenges)
        
        selected = prompt_for_category(pending_categories)
        state_manager.update(challenges, connector, selected = selected)
        
        state_manager.save_state()
    finally:
        os.chdir(caller_cwd)