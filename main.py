import feedparser
import time
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import osm_API


feed_url = "http://resultmaps.neis-one.org/newestosmcountryfeed?c=Croatia"

test_feed_file = "newestosmcountryfeed.atom"
saved_usernames_file = "saved_usernames.txt"


# Function to load previously saved usernames
def load_saved_usernames(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Function to save usernames to a file (sorted and unique)
def save_usernames(file_path, usernames):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("\n".join(sorted(usernames)))

def read_message_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None


if __name__ == "__main__":

    rss_feed = feedparser.parse(feed_url)
    
    # Parse the RSS feed from the test file
    #with open(test_feed_file, "r", encoding="utf-8") as file:
    #    rss_feed_content = file.read()

    #rss_feed = feedparser.parse(rss_feed_content)

    # Extract usernames from the feed
    extracted_usernames = set()
    for entry in rss_feed.entries:
        user_id = entry.link if "link" in entry else None
        if user_id and user_id.startswith("https://osm.org/user/"):
            username = unquote(user_id.split("/")[-1])
            extracted_usernames.add(username)

    # Load previously saved usernames
    saved_usernames = load_saved_usernames(saved_usernames_file)
    new_usernames = extracted_usernames - saved_usernames
    all_usernames = saved_usernames | extracted_usernames

    save_usernames(saved_usernames_file, all_usernames)

    if new_usernames:
        print(f"New usernames found:{new_usernames}. Sending welcome messages.")

        message_body = read_message_from_file("welcome_mail.txt")
        title = "Pozdrav od hrvatskog ogranka OSM zajednice"

        for index, recipient in enumerate(new_usernames):            
            if message_body:
                osm_API.send_message_to_user(recipient, title, message_body)
                
            if index < len(new_usernames) - 1:
                time.sleep(2)

    else:
        print("No new usernames found.")


 
