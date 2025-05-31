from bs4 import BeautifulSoup
from .base_website import WebsiteConnectorBase

class WebsiteCyberChallenge(WebsiteConnectorBase):
    def __init__(self, base_url, username, password):
        super().__init__(base_url, username, password)
        
        # Specific URL
        self.login_path = "/api/login"
        self.challenges_path = "/api/challenges"
        self.token = None       # Get this after login
        self.files_token = None # Get this after login
        
        self.current_user = '/api/currentUser'
        self.my_name = 'DUMMY NAME'
    
    def _get_display_name(self):
        if not self.logged_in:
            print("[CYBERCHALLENGE] Login first")
            return None
        
        api_url = self.base_url + self.current_user
        headers = {
            "Authorization": f"Token {self.token}"
        }
        user_response = self._get_page_content(api_url, headers = headers)
        
        if not user_response:
            print(f"[CYBERCHALLENGE] Cannot GET user at {api_url}")
            return None
        
        try:
            data = user_response.json()
        except ValueError: # requests.exceptions.JSONDecodeError
            print(f"[CYBERCHALLENGE] Cannot decode JSON: {api_url}")
            return None
        
        if 'name' not in data or 'surname' not in data:
            print(f"[CYBERCHALLENGE] Cannot find 'name' or 'surname'")
            return None
        
        self.display_name = data['name'] + ' ' + data['surname']
    
    def login(self):
        if not self.username or not self.password:
            print("[CYBERCHALLENGE] Missing credentials")
            return False
        
        login_url = self.base_url + self.login_path
        
        try:
            payload = {
                'email': self.username,
                'password': self.password
            }
            
            response = self.session.post(login_url, json=payload, allow_redirects=True)
            response.raise_for_status()
            
            try:
                data = response.json()
            except ValueError: # requests.exceptions.JSONDecodeError
                print(f"[CYBERCHALLENGE] Cannot decode JSON: {login_url}")
                return False
            
            if 'token' not in data or 'filesToken' not in data:
                print(f"[CYBERCHALLENGE] Cannot find 'token' or 'filesToken'")
                return False
            
            self.token = data['token']
            self.files_token = data['filesToken']
            self.logged_in = True
            
            # Get display name
            self._get_display_name()
            
            return True
        except Exception as e:
            print(f'[CYBERCHALLENGE] Unexpected error: {e}')
            
    def get_challenges(self):
        if not self.logged_in:
            print("[CYBERCHALLENGE] Login first")
            return None
        
        api_url = self.base_url + self.challenges_path
        
        headers = {
            "Authorization": f"Token {self.token}"
        }
        challenges_response = self._get_page_content(api_url, headers = headers)
        
        if not challenges_response:
            print(f"[CYBERCHALLENGE] Cannot GET challenges at {api_url}")
            return None
        
        try:
            data = challenges_response.json()
        except ValueError: # requests.exceptions.JSONDecodeError
            print(f"[CYBERCHALLENGE] Cannot decode JSON: {api_url}")
            return None
        
        if 'events' not in data:
            print(f"[CYBERCHALLENGE] Cannot find 'events'")
            return None
        
        events = data['events']
        parsed_challenges = []
        to_keep = ["title", "currentScore", "currentAffiliationSolves", "tags"]
        for ev in events:
            if 'sections' not in ev:
                print(f"[CYBERCHALLENGE] Cannot find 'sections', skipping event {ev['name']}")
                continue
            
            sections = ev['sections']
            for sec in sections:
                if 'challenges' not in sec:
                    print(f"[CYBERCHALLENGE] Cannot find 'sections', skipping event {ev['name']}")
                    continue
                
                challenges_list = sec['challenges']
                for c in challenges_list:
                    chal = {}
                    
                    # build ID separately
                    chal['id'] = c['id']
                    chal['name'] = c['title'] # Use same naming from other website
                    chal['value'] = c['currentScore']
                    chal['solves'] = c['currentAffiliationSolves']
                    chal['category'] = sec['name']
                    
                    parsed_challenges.append(chal)
                    
        return parsed_challenges
                
    def get_challenge_details(self, challenge_id):
        challenge_api_url = f"{self.base_url}{self.challenges_path}/{challenge_id}"
        
        headers = {
            "Authorization": f"Token {self.token}"
        }
        data_response = self._get_page_content(challenge_api_url, headers = headers)
        
        if not data_response:
            print(f"[CYBERCHALLENGE] Cannot get info for the challenge {challenge_id}")
            return None, None
        
        try:
            chal_data_json = data_response.json()
        except ValueError:
             print(f"[CYBERCHALLENGE] Cannot decode JSON for challenge {challenge_id}")
             return None, None
         
        parsed_details = {}
        parsed_details['id'] = chal_data_json['id']
        parsed_details['name'] = chal_data_json['title']
        parsed_details['value'] = chal_data_json['currentScore']
        parsed_details['description'] = chal_data_json['description']
        parsed_details['solves'] = chal_data_json['currentAffiliationSolves']
        
        # Parse attchements
        files = []
        for f in chal_data_json['files']:
            files.append(f['url'])
        parsed_details['files'] = files
        
        # Solvers
        parsed_solvers = []
        for solver in chal_data_json['solves']:
            if 'displayedName' in solver:
                parsed_solvers.append(solver['displayedName'])
                
        parsed_details['solved_by_me'] = self.my_name in parsed_solvers            
                
        return parsed_details, parsed_solvers
        
    def download_attachment(self, file_relative_url):
        if not self.logged_in:
            print("[CYBERCHALLENGE] Login first")
            return None
        
        if not file_relative_url.startswith('/'):
            file_relative_url = '/' + file_relative_url
        
        full_file_url = self.base_url + file_relative_url
        file_response = self._get_page_content(full_file_url)
        if file_response:
            return file_response.content
        else:
            print(f'[CYBERCHALLENGE] Error while downloading {full_file_url}')
            return None