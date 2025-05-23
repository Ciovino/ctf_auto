from bs4 import BeautifulSoup
import requests
import configparser

class WebsiteConnector:
    def __init__(self, base_url, config_file='config.ini'):
        self.base_url = base_url
        self.login_url = f"{base_url}/login"
        self.challeges_url = f'{base_url}/challenges'
        self.api_url = f'{base_url}/api/v1/challenges'
        
        self.session = requests.Session()
        self.logged_in = False
        
        self.config_file = config_file
        self.username = None
        self.password = None
        
        self._load_credentials()

    def _load_credentials(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        try:
            self.username = config['credentials']['username']
            self.password = config['credentials']['password']
        except KeyError:
            print("Cannot find section 'credentials' in the config file.")
            self.username = None
            self.password = None

    def _get_page(self, url):
        try:
            response = self.session.get(url, allow_redirects = True)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request at {url}: {e}")
            return None

    def login(self):
        if not self.username or not self.password:
            print("No credentials found. Please check the config.ini file")
            return False

        try:
            # Obtain nonce
            login_page_response = self._get_page(self.login_url)
            if not login_page_response:
                print("Error during the login")
                return False
            
            soup = BeautifulSoup(login_page_response.text, 'html.parser')
            
            # Find nonce
            # Used in the payload when doing a normal login
            nonce_input = soup.find('input', {'name': 'nonce'})
            if nonce_input and 'value' in nonce_input.attrs:
                nonce_value = nonce_input['value']
            else:
                print("Cannot find nonce")
                return False

            # Build the payload
            login_data = {
                'name': self.username,
                'password': self.password,
                '_submit': 'Invia',
                'nonce': nonce_value
            }

            # Send post for the login
            response = self.session.post(self.login_url, data=login_data, allow_redirects=True)
            response.raise_for_status()

            # Check the login
            if response.url == self.challeges_url:
                # print(f"Login successfull. Redirecting to {response.url}")
                self.logged_in = True
                return True
            else:
                print(f'Error during the login. Final URL: {response.url}')
                print(f'Final status code: {response.status_code}')                
                return False

        except requests.exceptions.RequestException as e:
            print(f"Connection error during login: {e}")
            return False
        except Exception as e:
            print(f'Unexpected error: {e}')
            return False
    
    def get_challenges(self):
        if not self.logged_in:
            print("Login first")
            return None
        
        challenges_response = self._get_page(self.api_url)
        if not challenges_response:
            print("Cannot GET challenges page")
            return None
        data = challenges_response.json()
        
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
    
    def challenge_info(self, id) -> tuple[dict, dict]:
        data = self._get_page(self.api_url + '/' + str(id))
        solves = self._get_page(self.api_url + '/' + str(id) + '/solves')
        
        if not data and not solves:
            print("Cannot GET challenges info")
            return None, None
        
        chal_data = data.json().get('data', dict())
        chal_solves = solves.json().get('data', [])
        
        # Parsing challenge data
        data_to_keep = ["id", "name", "value", "description", "solves", "solved_by_me", "category", "files"]
        parsed = {}
        for field in data_to_keep:
            if field in chal_data:
                parsed[field] = chal_data[field]
        
        # Parsing solvers' name
        parsed_solvers = []
        for solver in chal_solves:
            parsed_solvers.append(solver['name'])
            
        return parsed, parsed_solvers
    
    def download_attachments(self, file_url):
        file = self._get_page(self.base_url + '/' + file_url)
        if file:
            return file.content
        else:
            print('Cannot download file')
            return None