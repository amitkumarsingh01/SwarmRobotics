import requests

# Path to the file on Pi 1 that needs to be sent
file_path = '/path/to/your/file.txt'

# Server (laptop) IP address and endpoint
server_url = 'http://192.168.202.176:5000/upload'

# Open the file in binary mode
with open(file_path, 'rb') as f:
    file_data = {'file': f}
    try:
        response = requests.post(server_url, files=file_data)
        if response.status_code == 200:
            print('File successfully sent to the laptop.')
        else:
            print(f"Failed to send file. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error occurred: {e}")