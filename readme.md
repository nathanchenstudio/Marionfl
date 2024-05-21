A spider that scrapes permits from marionfl.org. A customer download handler is used to emulate browser fingerprinting.

This spider project is intended for informational and educational purposes only. It is not intended to be used for commercial purposes or to violate any laws. The authors of this project do not endorse or promote any illegal activities. By using this project, you agree to use it responsibly and in compliance with all applicable laws and regulations. The authors are not responsible for any misuse or legal consequences arising from the use of this project.

# Deployment guide

1. Install Python 3.11

2. Open a CMD window, enter the project's root directory, e.g.
   
   ```
   cd ~/codes/Marionfl
   ```

3. Create a virtual Python3 environment and activate it. e.g.:
   
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install the required libraries:
   
   ```
   pip install -r requirements.txt
   ```


5. Change the variable "PROXY_URL" in "settings.py" to use a proxy:
   
   ```
   PROXY_URL = 'http://YOUR_PROXY_IP:PORT'
   ```

---

# How to run the spider

1. Open a CMD window, enter the project's root directory, e.g.
   
   ```
   cd ~/codes/Marionfl
   ```

2. Activate its virtual Python3 environment. e.g.:
   
   ```
     source .venv/bin/activate
   ```

3. Run the following commands to start the spider:
   
   ```
   scrapy crawl marionfl
   ```