from abc import ABC, abstractmethod
import requests

class WebsiteConnectorBase(ABC):

    def __init__(self, base_url, username=None, password=None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        
        self.session = requests.Session()
        self.logged_in = False

    def _get_page_content(self, url):
        # Normal GET request
        try:
            response = self.session.get(url, allow_redirects=True)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error during GET from {url}: {e}")
            return None

    @abstractmethod
    def login(self):
        # Login to the website
        pass

    @abstractmethod
    def get_challenges(self):
        # Get challenges list
        pass

    @abstractmethod
    def get_challenge_details(self, challenge_id):
        # Challenge details, from id
        pass

    @abstractmethod
    def download_attachment(self, file_relative_url):
        # Download any attachments
        pass