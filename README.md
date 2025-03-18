Unfake is a Chrome extension designed to help users detect fake news on X (formerly Twitter). It integrates AI, user voting, and credibility scoring to provide reliable news verification directly within your browser.

Project Components
This project consists of:
AI Model and Checked Algorithm API
Blockchain API
Scraper API
Unfake Chrome Extension

**All APIs must be run locally. The extension can be downloaded from the website or GitHub.

Local API Setup Instructions
1. Clone the Repositories
Clone the following 3 API repositories into separate folders:

AI Model API (Flask backend with BERT model)
Blockchain API
Scraper API (Tweet scraping with Playwright)

git clone https://github.com/DamieIsBreadie/Unfake_AIModel
git clone https://github.com/DamieIsBreadie/blockchain_transactions
git clone https://github.com/DamieIsBreadie/Unfake_Scraper


2. Install Dependencies
Typical dependencies include:
Flask
Flask-Cors
torch
transformers
firebase-admin
playwright

For scraper, install Playwright browser:
playwright install


3. Run the APIs Locally
Each API should run on a different port:
python api.py       # For Blockchain API (default port 5002)
python main.py       # For AI Model API (default port 5001)
python app.py        # For Scraper API (default port 5000)

Ensure that:
serviceAccountKey.json is placed correctly for Firebase operations.
Ports 5000, 5001, and 5002 are open and not blocked by firewalls.


Chrome Extension Installation Guide
1. Download the Extension
Option 1: Download the ZIP from the official website.
Option 2: Clone or download the extension folder from GitHub:
git clone https://github.com/RraraA/UnfakeEx


2. Unzip (if downloaded as ZIP)
Extract the folder to a location of your choice.

3. Load the Extension into Chrome
Open chrome://extensions
Toggle Developer Mode (top right)
Click "Load unpacked"
Select the extracted extension folder

**The Unfake Extension is now installed and ready to use on X (Twitter).

Reminder
The extension communicates with the local APIs. Make sure all servers (5000, 5001, 5002) are running before testing.
Firebase credentials must be configured correctly.
Developer Mode must stay ON for the extension to work.

