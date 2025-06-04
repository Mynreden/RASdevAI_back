import httpx

BASE_URL = "http://localhost:8000/api"  # change if your FastAPI app runs on a different port
HEADERS = {"X-User-Email": "rulik_2004@mail.ru"}  # use your test user email

def test_portfolio_history():
    response = httpx.get(f"{BASE_URL}/portfolio/history", headers=HEADERS, timeout=30)
    print(response)
    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", response.json())
    except Exception as e:
        print("Failed to parse JSON:", e)
        print("Response Text:", response.text)

if __name__ == "__main__":
    test_portfolio_history()
