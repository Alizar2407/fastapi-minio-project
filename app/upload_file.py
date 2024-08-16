import requests

presigned_url = "upload_link"

file_path = "file_path"

with open(file_path, "rb") as file_data:
    response = requests.put(presigned_url, data=file_data)

if response.status_code == 200:
    print("File uploaded successfully")
else:
    print(f"Error uploading file: {response.status_code}")
    print(response.text)
