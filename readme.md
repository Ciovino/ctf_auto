# CTF Challenge Automator (CTF_AUTO)

Automatically fetch and manage Capture The Flag (CTF) challenges from multiple supported CTF platforms. This tool helps you keep local copies of challenge information, descriptions, solver lists, and attachments, organized neatly on your filesystem.

## Features

* **Multi-Platform Support**: Easily extendable to support various CTF platforms through a connector-based architecture.
* **Centralized Configuration**: Manage global settings (like save directories) and site-specific credentials/details via a single `config.ini` file.
* **Automatic Downloads**: Fetches challenge descriptions, points, solve counts, solver lists, and attachments.
* **Organized Folder Structure**: Saves challenges in a structured way: `MAIN_DIRECTORY/PLATFORM_NAME/CATEGORY_NAME/CHALLENGE_NAME/`.
* **State Management**: Keeps track of challenge updates to only download new or modified information.

## Prerequisites

* Python 3 (version 3.7 or newer recommended)
* `pip` (Python package installer)
* `venv` (Python virtual environment module, usually included with Python 3)

## Setup and Configuration

1.  **Clone the Repository** (If you haven't already):
    ```bash
    git clone https://github.com/Ciovino/ctf_auto.git
    cd ctf_auto
    ```

2.  **Install dependencies**:
    * Create a Python virtual environment.
    * Install the required Python packages from `requirements.txt`.

3.  **Configure `config.ini`**:
    * If `config.ini` does not exist in the script's directory, you might to create it from `config.ini.example`.
    * Open `config.ini` and configure it according to your needs. It has two main types of sections:

    * **Global Settings**:
        ```ini
        [global_settings]
        main_challenges_dir = ../ctf_challenges  ; Main directory to save all CTF data
        state_file_name = challenge_tracker.json ; Name of the state file
        ```

    * **Platform-Specific Settings**: Add a section for each CTF platform you want to use.
        ```ini
        [platform_example]
        enabled = true
        base_url = https://ctfplatform.com
        username = your_username
        password = your_password
        connector = website_connectors.platform_connector.PlatformConnector
        ```
        * Replace placeholder values with your actual details.
        * The `connector` should be the full Python path to the connector class for that platform (e.g., `folderName.fileName.ClassName`).

## Usage

Once setup and configuration are complete, run the script:

```bash
python main.py
```
The program will:
1. Read the config.ini.
2. Connect to each enabled platform and attempt to log in.
3. Fetch the list of challenges.
4. Compare with its stored state to find new or updated challenges.
5. Prompt you to choose which platforms/categories to update.
6. Download information and files for the selected challenges.

## Folder Structure
Challenges are organized as follows:
``` bash
../ctf_challenges/
├── challenge_tracker.json      # Stores the state of downloaded challenges
│
├── molecon_ctfd/               # Challenges from the 'molecon_ctfd' platform
│   ├── Web/
│   │   └── SuperSecureLogin/
│   │       ├── general_info.md # Description, points, category, solved status
│   │       ├── solvers.txt     # List of users who solved it
│   │       └── challenge/      # Contains downloaded attachments
│   │           └── login_page.zip
│   ├── Pwn/
│   │   └── ...
│   └── ...
│
├── another_platform_example/   # Challenges from another platform
│   ├── Crypto/
│   │   └── ...
│   └── ...
│

project_root_directory/         # Your cloned repository
├── website_connectors/
│   ├── base_website.py
│   ├── molecon.py
│   └── ... (other custom connectors)
├── config.ini
├── main.py
├── challenge_state_manager.py
├── requirements.txt
└── README.md
```

Inside each challenge folder (e.g., SuperSecureLogin/):
* `general_info.md`: Contains the challenge name, ID, platform, category, points, solved status, and description.
* `solvers.txt`: Lists users who have solved the challenge and the total solve count.
* `challenge/`: A subfolder containing any downloadable attachments for the challenge.

## How It Works
* *Pending Challenges*: A challenge is considered "pending" an update if its point value, number of solves, or your "solved by me" status has changed since the last check, or if it's entirely new.
* *Updates*: When updating a challenge:
    - `general_info.md` and `solvers.txt` are overwritten with the latest information.
    - Attachments are typically downloaded into the `challenge/` subfolder if the subfolder is newly created for that challenge. Existing files in `challenge/` are generally not overwritten unless specific logic is added for it.
* *Scope*: You can choose to update all pending challenges or filter by a specific platform/category.

## Adding New CTF Platforms
This tool is designed to be extensible:
1. **Create a Connector Class**:
    * Develop a new Python class that inherits from `website_connectors.base_website.WebsiteConnectorBase`.
    * Implement all the abstract methods defined in the base class (e.g., `login()`, `get_challenges()`, `get_challenge_details()`, `download_attachment()`) with the specific logic for the new CTF platform.
    * Place your new connector file (e.g., `my_new_site_connector.py`) inside the `website_connectors/` directory. Make sure this directory has an `__init__.py` file to be treated as a package.
2. **Configure in `config.ini`**:
    * Add a new section for your platform (e.g., [my_new_site]).
    * Set `enabled = true`.
    * Provide `base_url` and any necessary authentication details (e.g., `username`, `password`, `api_key`).
    * Set `connector_class` to the full path of your new class, for example: `website_connectors.my_new_site_connector.MyNewSiteConnectorClass`.

## Notes
* Ensure your `requirements.txt` is up-to-date, especially if you add new connectors that have specific Python package dependencies. To update the requirements file you can run `pip freeze > requirements.txt`
