# Nitter Monitor

## Overview
The `nitter.py` script is a monitoring tool designed to parse RSS feeds, process URLs, and optionally store them in a database for further analysis. It can also operate through a Tor proxy for enhanced privacy.

## Features
- **RSS Monitoring**: Periodically checks RSS feeds for updates.
- **URL Processing**: Identifies, defangs, and normalizes URLs found in RSS entries.
- **Logging**: Logs all activities and errors for debugging and monitoring.
- **Tor Proxy Support**: Routes network requests through the Tor network for anonymity.

## Prerequisites

### Required Software
- **Python 3.8+**
- **Tor**

#### Python Dependencies
Install the necessary Python packages:
```bash
pip install -r requirements.txt
```

#### Installing Tor
1. Install Tor using the package manager:
   ```bash
   sudo apt update
   sudo apt install tor -y
   ```

2. Start and enable the Tor service:
   ```bash
   sudo systemctl start tor
   sudo systemctl enable tor
   ```

3. Verify Tor is working by checking your IP address through the Tor network:
   ```bash
   curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org
   ```
   If successful, you will see a message confirming that you are using the Tor network.

### Configuration

#### Configuration File
Ensure `config.py` contains the following parameters:
- `LOG_DIR`: Directory for storing logs.
- `NITTER_LOG`: Log file name for the script.
- `NITTER_FEEDS`: A list of RSS feed configurations with the following structure:
  ```python
  NITTER_FEEDS = [
      {
          "url": "<RSS feed URL>",
          "name": "<Feed name>"
      },
      # Add more feeds as needed
  ]
  ```

#### Tor Proxy Configuration
The script uses the following Tor proxy settings:
```python
PROXIES = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050",
}
```
Ensure the Tor service is running for these settings to work.

## Usage

### Running the Script
Run the `nitter.py` script with Python:
```bash
python nitter.py
```

### Logs
Logs are saved in the directory specified by the `LOG_DIR` parameter in `config.py`. Each run of the script will append new log entries to the specified log file.

### Scheduling
Use a scheduling tool like `cron` to periodically execute the script. For example:
1. Open the `crontab` editor:
   ```bash
   crontab -e
   ```
2. Add an entry to run the script every hour:
   ```bash
   0 * * * * /usr/bin/python3 /path/to/nitter.py
   ```

## Notes
- Ensure RSS feed URLs are valid and accessible.
- Make sure the Tor service is active before running the script.
- Verify that `config.py` is properly configured for your environment.

## Debugging
If you encounter issues:
1. Check the log file for errors.
2. Ensure Tor is running and properly configured.
3. Validate the structure of `config.py`.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

