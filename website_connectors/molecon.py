from bs4 import BeautifulSoup
from .base_website import WebsiteConnectorBase

class WebsiteMolecon(WebsiteConnectorBase):
    def __init__(self, base_url, username, password):
        super().__init__(base_url, username, password)
        
        # Specific URL
        self.login_path = "/login"
        self.challenges_api_path = "/api/v1/challenges"
        
    def login(self):
        if not self.username or not self.password:
            print("[MOLECON] Missing credentials")
            return False

        login_url = self.base_url + self.login_path
        challenges_url = self.base_url + "/challenges"

        try:
            login_page_response = self._get_page_content(login_url)
            if not login_page_response:
                print(f"[MOLECON] Error during login at {login_url}")
                return False
            
            soup = BeautifulSoup(login_page_response.text, 'html.parser')
            nonce_input = soup.find('input', {'name': 'nonce'})
            if nonce_input and 'value' in nonce_input.attrs:
                nonce_value = nonce_input['value']
            else:
                print("[MOLECON] Cannot find nonce")
                return False

            login_data = {
                'name': self.username,
                'password': self.password,
                '_submit': 'Invia',
                'nonce': nonce_value
            }

            response = self.session.post(login_url, data=login_data, allow_redirects=True)
            response.raise_for_status()

            if response.url.startswith(challenges_url):
                self.logged_in = True
                return True
            else:
                print(f'[MOLECON] Error during the login. Final URL: {response.url}')
                print(f'[MOLECON] Final status code: {response.status_code}')                   
                return False

        except Exception as e:
            print(f'[MOLECON] Unexpected error: {e}')
            return False
    
    def get_challenges(self):
        if not self.logged_in:
            print("[MOLECON] Login first")
            return None
        
        api_url = self.base_url + self.challenges_api_path
        challenges_response = self._get_page_content(api_url)
        
        if not challenges_response:
            print(f"[MOLECON] Cannot GET challenges page at {api_url}")
            return None
        
        try:
            data = challenges_response.json()
        except ValueError: # requests.exceptions.JSONDecodeError
            print(f"[MOLECON] Cannot decode JSON: {api_url}")
            return None

        challenges_list = data.get("data", [])
        parsed_challenges = []
        to_keep = ["id", "name", "value", "solves", "solved_by_me", "category"]
        for chal in challenges_list:
            modified = {}
            for field in to_keep:
                if field in chal:
                    modified[field] = chal[field]
            parsed_challenges.append(modified)
            
        return parsed_challenges
    
    def get_challenge_details(self, challenge_id):
        if not self.logged_in:
            print("[MOLECON] Login first")
            return None, None

        challenge_api_url = f"{self.base_url}{self.challenges_api_path}/{challenge_id}"
        solves_api_url = f"{self.base_url}{self.challenges_api_path}/{challenge_id}/solves"
        
        data_response = self._get_page_content(challenge_api_url)
        solves_response = self._get_page_content(solves_api_url)
        
        if not data_response or not solves_response:
            print(f"[MOLECON] Cannot get info for the challenge {challenge_id}")
            return None, None
        
        try:
            chal_data_json = data_response.json()
            chal_solves_json = solves_response.json()
        except ValueError:
             print(f"[MOLECON] Cannot decode JSON for challenge {challenge_id}")
             return None, None

        chal_data = chal_data_json.get('data', {})
        chal_solves = chal_solves_json.get('data', [])
        
        data_to_keep = ["id", "name", "value", "description", "solves", "solved_by_me", "category", "files"]
        parsed_details = {}
        for field in data_to_keep:
            if field in chal_data:
                parsed_details[field] = chal_data[field]
        
        parsed_solvers = []
        for solver in chal_solves:
            if 'name' in solver:
                parsed_solvers.append(solver['name'])
            
        return parsed_details, parsed_solvers
    
    def download_attachment(self, file_relative_url):
        if not self.logged_in:
            print("[MOLECON] Login first")
            return None
        
        if not file_relative_url.startswith('/'):
            file_relative_url = '/' + file_relative_url
            
        full_file_url = self.base_url + file_relative_url
        
        file_response = self._get_page_content(full_file_url)
        if file_response:
            return file_response.content
        else:
            print(f'[MOLECON] Error while downloading {full_file_url}')
            return None