import asyncio
import httpx

async def test_lstm_forecast():
    base_url = "http://localhost:8000/api"  # Replace with your FastAPI host if different
    ticker = "AIRA"
    forecast_days = 5

    url = f"{base_url}/forecast/{ticker}"
    params = {"forecast_days": forecast_days}
    print(f"Requesting prediction for {ticker} with {forecast_days} days forecast...", url)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ Prediction successful:")
                print(data)
            else:
                print("❌ Failed to get prediction:")
                print(response.text)

        except Exception as e:
            print(f"❌ Request failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_lstm_forecast())
