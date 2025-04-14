import json
import os

class ChallengeStateManager:
    def __init__(self, state_file = 'challenge_state.json'):
        self.state_file = state_file
        self.state = self.load_state()
        
    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding = 'utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print('Error when opening the state file: ', e)
                return {}
        return {}
    
    def save_state(self):
        try:
            with open(self.state_file, 'w', encoding = 'utf-8') as f:
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
    
    def update(self, challenges, selected = ''):
        if selected is None:
            return
        
        new_state = []
        for chal in challenges:
            id = chal['id']
            if not chal['pending']:
                new_state.append(self.get_challenge_by_id(id))
            if selected == '' or chal['category'] == selected:
                chal['pending'] = False
                new_state.append(chal)
                
        self.state = new_state
    
    def get_challenge_by_id(self, id):
        for chal in self.state:
            if chal['id'] == id:
                return chal
        return {}