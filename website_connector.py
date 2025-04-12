from bs4 import BeautifulSoup
import requests
import configparser

class WebsiteConnector:
    def __init__(self, base_url, config_file='config.ini'):
        self.base_url = base_url
        self.login_url = f"{base_url}/login"
        self.challeges_url = f'{base_url}/challenges'
        
        self.session = requests.Session()
        
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

    def login(self):
        if not self.username or not self.password:
            print("No credentials found. Please check the config.ini file")
            return False

        try:
            # Obtain nonce
            login_page_response = self.session.get(self.login_url)
            login_page_response.raise_for_status()
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
                print(f"Login successfull. Redirecting to {response.url}")
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