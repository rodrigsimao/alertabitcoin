import os
import requests

CMC_API_KEY = os.environ.get("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
print("DEBUG - API KEY:", "ENCONTRADA" if CMC_API_KEY else "NÃO ENCONTRADA")

def get_btc_price():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

    # 1ª chamada: USD
    r_usd = requests.get(url, params={"symbol": "BTC", "convert": "USD"}, headers=headers, timeout=10)
    r_usd.raise_for_status()
    price_usd = r_usd.json()["data"]["BTC"]["quote"]["USD"]["price"]

    # 2ª chamada: BRL
    r_brl = requests.get(url, params={"symbol": "BTC", "convert": "BRL"}, headers=headers, timeout=10)
    r_brl.raise_for_status()
    price_brl = r_brl.json()["data"]["BTC"]["quote"]["BRL"]["price"]

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
        error_msg = f"⚠️ Erro ao buscar cotação BTC: {e}"
        print(error_msg)
        try:
            send_telegram(error_msg)
        except:
            pass

if __name__ == "__main__":
    main()

