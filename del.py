import requests

# Config
url = "http://localhost:8000/api/portfolio/history/60"
headers = {
    "accept": "application/json",
    "X-User-Email": "rulik_2004@mail.ru"  # Replace with actual email
}

# Make request
response = requests.get(url, headers=headers)

# Handle response
if response.status_code == 200:
    data = response.json()
    print("Portfolio History:")
    print(data)
    for entry in data:
        print(entry)
else:
    print(f"Error {response.status_code}: {response.text}")
