import os
import requests

# URL to download files from the laptop's public folder
download_url = 'http://192.168.202.176:5000/download'
save_directory = '/home/edwin/pi/' #Save directory

# Create the directory if it doesn't exist
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

try:
    # Request the file list from the laptop
    response = requests.get(download_url)
    if response.status_code == 200:
        file_list = response.json()  # Assuming the server returns a list of filenames
        for file_name in file_list:
            file_url = f"{download_url}/{file_name}"
            file_response = requests.get(file_url)
            if file_response.status_code == 200:
                with open(os.path.join(save_directory, file_name), 'wb') as f:
                    f.write(file_response.content)
                print(f"Downloaded {file_name} to {save_directory}")
            else:
                print(f"Failed to download {file_name}")
    else:
        print(f"Failed to retrieve file list. Status code: {response.status_code}")
except Exception as e:
    print(f"Error occurred: {e}")