import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

# ==== CONFIG ====
CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
SYMBOL = "BTC"

# ==== FUNÇÕES ====
def get_btc_price():
    params = {"symbol": SYMBOL, "convert": "USD"}
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    r = requests.get(URL, params=params, headers=headers)
    r.raise_for_status()
    data = r.json()
    return data["data"][SYMBOL]["quote"]["USD"]["price"]

def save_price(price):
    filename = "btc_history.csv"
    now = datetime.now(pytz.timezone("America/Sao_Paulo"))
    row = {"datetime": now.strftime("%Y-%m-%d %H:%M:%S"), "price": price}
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(filename, index=False)
    return df

def plot_chart(df):
    plt.figure(figsize=(10, 5))
    plt.plot(df["datetime"], df["price"], marker="o")
    plt.xticks(rotation=45)
    plt.title("Histórico do Bitcoin (USD)")
    plt.tight_layout()
    filename = "btc_chart.png"
    plt.savefig(filename)
    plt.close()
    return filename

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    r = requests.post(url, data=payload)
    r.raise_for_status()

def send_telegram_photo(photo_path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
        r = requests.post(url, files=files, data=data)
        r.raise_for_status()

# ==== MAIN ====
def main():
    tz = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(tz)
    current_time = now.strftime("%H:%M")

    # Só dispara exatamente às 06:00 ou 13:00
    if current_time not in ["06:00", "13:00"]:
        print(f"[INFO] Agora {current_time} Brasília -> fora do horário de envio.")
        return

    print(f"[INFO] Horário válido {current_time}, enviando alerta...")

    # Captura preço
    price = get_btc_price()
    df = save_price(price)
    chart = plot_chart(df)

    # Mensagem
    msg = f"📈 Atualização BTC\nPreço: ${price:,.2f}\nHorário: {now.strftime('%d/%m/%Y %H:%M')}"
    send_telegram_message(msg)
    send_telegram_photo(chart, caption="Gráfico BTC")

if __name__ == "__main__":
    main()
