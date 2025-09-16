import os
import requests
print("DEBUG - API KEY length:", len(CMC_API_KEY) if CMC_API_KEY else "NÃO ENCONTRADA")
CMC_API_KEY = os.environ.get("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_btc_price():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    # Agora pedimos USD e BRL juntos
    params = {"symbol": "BTC", "convert": "USD,BRL"}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    price_usd = data["data"]["BTC"]["quote"]["USD"]["price"]
    price_brl = data["data"]["BTC"]["quote"]["BRL"]["price"]
    return price_usd, price_brl

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

def main():
    try:
        price_usd, price_brl = get_btc_price()
        text = (
            f"💰 Bitcoin (BTC)\n"
            f"Cotação atual:\n"
            f"🇺🇸 USD: ${price_usd:,.2f}\n"
            f"🇧🇷 BRL: R${price_brl:,.2f}"
        )
        send_telegram(text)
        print("Mensagem enviada:\n", text)
    except Exception as e:
        print("Erro:", e)

if __name__ == "__main__":

    main()

