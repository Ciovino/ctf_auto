from website_connector import WebsiteConnector

if __name__ == "__main__":
    base_url = "https://cc-ctfd.m0lecon.it"
    connector = WebsiteConnector(base_url)
    
    if connector.login():
        print("Logged in :)")
    else:
        print("Login failed :(")
        exit(-1)
        
    print(connector.get_categories())