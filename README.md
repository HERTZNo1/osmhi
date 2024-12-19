# osmhi

## Environment Setup
1. Create a virtual environment:
    ```bash
    python -m venv osmhi
    ```
2. Activate the virtual environment:
    ```bash
    source osmhi/bin/activate
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Register a New OAuth Application at osm.org
1. Navigate to [osm.org](https://www.openstreetmap.org) and register a new OAuth application with the following details:
    - **Name**: Welcome mail script
    - **Redirect URIs**: `http://127.0.0.1:8080/callback`
    - **Scopes**:
        - `read_prefs`
        - `consume_messages`
        - `send_messages`

2. After registration, note down the `CLIENT_ID` and `CLIENT_SECRET`.

## Create `.env` File
1. In the project directory, create a `.env` file.
2. Add the following content, replacing `...` with the values from the OAuth application:
    ```plaintext
    CLIENT_ID=...
    CLIENT_SECRET=...
    ```

## Running the Script
1. Activate the virtual environment:
    ```bash
    source osmhi/bin/activate
    ```
2. Run the script:
    ```bash
    python main.py
    ```

## Additional Files
- **`osm_tokens.json`**: This file stores the buffered access token for OSM.
- **`saved_usernames.txt`**: This file logs the usernames to whom the welcome mail has been sent.
