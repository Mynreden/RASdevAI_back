import asyncio
import httpx

async def test_monthly_lstm_forecast():
    base_url = "http://localhost:8000/api"  # Replace with your FastAPI host if different
    ticker = "AIRA"

    url = f"{base_url}/forecast/monthly/{ticker}"
    print(f"Requesting monthly prediction for {ticker}...")
    print(f"URL: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ Monthly prediction successful:")
                print(f"Ticker: {data.get('ticker')}")
                print(f"Predicted Price: ${data.get('predicted_price'):,.2f}")
                print(f"Predicted Direction: {'📈 UP' if data.get('predicted_direction') == 1 else '📉 DOWN'}")
                print(f"Prediction Type: {data.get('prediction_type')}")
                print("\nFull Response:")
                print(data)
            else:
                print("❌ Failed to get monthly prediction:")
                print(response.text)

        except Exception as e:
            print(f"❌ Request failed with error: {e}")

async def test_daily_lstm_forecast():
    base_url = "http://localhost:8000/api"  # Replace with your FastAPI host if different
    ticker = "AIRA"
    forecast_days = 5

    url = f"{base_url}/forecast/{ticker}"
    params = {"forecast_days": forecast_days}
    print(f"\nRequesting daily prediction for {ticker} with {forecast_days} days forecast...")
    print(f"URL: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            print(f"Request URL: {response.url}")
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("✅ Daily prediction successful:")
                print(f"Forecast Days: {data.get('forecast_days')}")
                print(f"Predicted Prices: {data.get('predicted_prices')}")
                print("\nFull Response:")
                print(data)
            else:
                print("❌ Failed to get daily prediction:")
                print(response.text)

        except Exception as e:
            print(f"❌ Request failed with error: {e}")

async def test_both_forecasts():
    """Test both monthly and daily forecasts"""
    print("=" * 50)
    print("TESTING LSTM FORECASTING ENDPOINTS")
    print("=" * 50)
    
    # Test monthly forecast
    await test_monthly_lstm_forecast()
    
    print("\n" + "=" * 50)
    
    # Test daily forecast
    await test_daily_lstm_forecast()
    
    print("\n" + "=" * 50)
    print("TESTING COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    # Test both endpoints
    #asyncio.run(test_both_forecasts())
    
    # Or test only monthly forecast
    asyncio.run(test_monthly_lstm_forecast())
    
    # Or test only daily forecast
    # asyncio.run(test_daily_lstm_forecast())