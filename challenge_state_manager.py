import json
import os
from urllib.parse import urlparse, unquote
from website_connector import WebsiteConnector

class ChallengeStateManager:
    def __init__(self, state_file = 'challenge_state.json', main_dir = '../ctf'):
        self.state_file = state_file
        self.challenges_directory = main_dir
        
        self.state = self.load_state()
    
    def full_path(self, path):
        return self.challenges_directory + '/' + path
    
    def load_state(self):
        # Check if main directory exists
        if not os.path.exists(self.challenges_directory):
            # create a new one
            os.makedirs(self.challenges_directory, exist_ok = True)
        
        if os.path.exists(self.full_path(self.state_file)):
            try:
                with open(self.full_path(self.state_file), 'r', encoding = 'utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print('Error when opening the state file: ', e)
                return {}
        return {}
    
    def save_state(self):
        try:
            with open(self.full_path(self.state_file), 'w', encoding = 'utf-8') as f:
                json.dump(self.state, f, indent = 4)
        except Exception as e:
            print('Error during saving the state file: ', e)
            
    def is_pending(self, new_data):
        challenge_id = new_data.get('id')
        if not challenge_id:
            print('Invalid challenge id. Cannot update the state')
            print(new_data)
            return False
        
        old_data = self.get_challenge_by_id(challenge_id)
        pending = old_data == {}
        
        for field in ['value', 'solves', 'solved_by_me']:
            if new_data.get(field) != old_data.get(field) or pending:
                pending = True
                break
        
        return pending
    
    def get_filename_from_url(url):
        path = urlparse(url).path
        filename = os.path.basename(path)
        return unquote(filename)
    
    def update(self, challenges, website: WebsiteConnector, selected = ''):
        if selected is None:
            return
        
        new_state = []
        for chal in challenges:
            id = chal['id']
            if not chal['pending']:
                new_state.append(self.get_challenge_by_id(id))
            if selected == '' or chal['category'] == selected:
                print(f'Saving: {chal['name']}')
                
                chal['pending'] = False
                cat = chal['category']
                chal_path = cat + '/' + chal['name']
                file_challenge = chal_path + '/' + 'challenge'
                update_file = False
                
                # create the category directory
                if not os.path.exists(self.full_path(cat)):
                    print(f'\t{cat} directory not found. Making a new one')
                    os.makedirs(self.full_path(cat), exist_ok = True)
                # create the challenge directory
                if not os.path.exists(self.full_path(chal_path)):
                    print(f'\t"{chal['name']}" directory not found. Making a new one')
                    os.makedirs(self.full_path(chal_path), exist_ok = True)
                # check if the 'challenge' folder exists
                # update file if the directory does not exists
                if not os.path.exists(self.full_path(file_challenge)):
                    print('\tChallenge directory not found. Making a new one')
                    os.makedirs(self.full_path(file_challenge), exist_ok = True)
                    update_file = True
                    
                # Call the api
                print(f'\tAsking for "{chal['name']}" info')
                chal_data, solvers = website.challenge_info(id)
                if not chal_data and not solvers:
                    continue
                
                # Update files
                # 1. general_info.md
                print('\tWriting "general_info.md"')
                with open(self.full_path(chal_path + '/general_info.md'), 'w') as f:
                    f.write(f'# ({chal_data['id']}) {chal_data['name']}\n')
                    f.write(f'- Category: {chal_data['category']}\n')
                    f.write(f'- {chal_data['value']} points\n')
                    f.write(f'- {'**Solved**' if chal_data['solved_by_me'] else '==Not== Solved'}\n\n')
                    f.write(f'## Description:\n{chal_data['description']}')
                
                # 2. solvers.txt
                print('\tWriting "solvers.txt"')
                with open(self.full_path(chal_path + '/solvers.txt'), 'w') as f:
                    f.write(f'{chal_data['solves']} people solved this:\n')
                    for solver in solvers:
                        f.write(f'\t{solver}\n')
                        
                # 3. download files
                if len(chal_data['files']) > 0 and update_file:
                    for file in chal_data['files']:
                        name = ChallengeStateManager.get_filename_from_url(file)
                        
                        print(f'\tDownloading "{name}"')
                        content = website.download_attachments(file)
                        if content is None:
                            continue
                        
                        with open(self.full_path(file_challenge + '/' + name), 'wb') as f:                        
                            f.write(content)
                
                new_state.append(chal)
                
        self.state = new_state
    
    def get_challenge_by_id(self, id):
        for chal in self.state:
            if chal['id'] == id:
                return chal
        return {}