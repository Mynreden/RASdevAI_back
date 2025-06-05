import httpx
import time

BASE_URL = "http://localhost:8000/api"
HEADERS = {"X-User-Email": "rulik_2004@mail.ru"}  # Simulate same user for memory

def send_message(message: str):
    response = httpx.post(
        f"{BASE_URL}/chat-gpt/",
        json={"message": message},
        headers=HEADERS,
        timeout=30
    )
    print(f"\nUSER: {message}")
    print("Status Code:", response.status_code)
    try:
        reply = response.json()
        print(f"GPT: {reply}")
    except Exception as e:
        print("Failed to parse JSON:", e)
        print("Response Text:", response.text)

def test_chat_gpt_kazakh_market_dialog():
    print("🧪 Starting dialog with ChatGPT (Kazakh market memory test)\n")

    send_message("What are the most popular stocks in the Kazakh market?")

    send_message("Remember that Kaspi.kz is one of the most traded stocks in Kazakhstan.")

    send_message("Which company did I say is one of the most traded stocks in Kazakhstan?")

    send_message("Who won the World Cup in 2022?")

    print("\n✅ Test finished.")

if __name__ == "__main__":
    test_chat_gpt_kazakh_market_dialog()
