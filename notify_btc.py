import os
import requests
import csv
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

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

def save_to_csv(price_usd, price_brl):
    """Salva o histórico em btc_history.csv"""
    filename = "btc_history.csv"
    file_exists = os.path.isfile(filename)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Cabeçalho só se for o primeiro registro
        if not file_exists:
            writer.writerow(["datetime_utc", "price_usd", "price_brl"])
        writer.writerow([now, f"{price_usd:.2f}", f"{price_brl:.2f}"])

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
        save_to_csv(price_usd, price_brl)
        print("Mensagem enviada e histórico salvo:\n", text)
    except Exception as e:
        error_msg = f"⚠️ Erro ao buscar cotação BTC: {e}"
        print(error_msg)
        try:
            send_telegram(error_msg)
        except:
            pass

if __name__ == "__main__":
    main()

df = pd.read_csv("btc_history.csv", parse_dates=["datetime_utc"])
plt.figure(figsize=(10,5))
plt.plot(df["datetime_utc"], df["price_usd"], label="USD")
plt.plot(df["datetime_utc"], df["price_brl"], label="BRL")
plt.xlabel("Data (UTC)")
plt.ylabel("Preço")
plt.title("Histórico do Bitcoin")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("btc_chart.png")
plt.close()
