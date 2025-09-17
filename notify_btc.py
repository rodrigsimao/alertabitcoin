import os
import requests
import csv
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

CMC_API_KEY = os.environ.get("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
VARIACAO_ALERTA = 5  # percentual de variação para alerta

# Horários para notificações regulares (UTC)
NOTIF_HORARIOS = ["10:00", "17:00", "00:00"]  # 06h, 13h, 20h horário Cuiabá (UTC-4)

def get_btc_price():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

    r_usd = requests.get(url, params={"symbol": "BTC", "convert": "USD"}, headers=headers, timeout=10)
    r_usd.raise_for_status()
    price_usd = r_usd.json()["data"]["BTC"]["quote"]["USD"]["price"]

    r_brl = requests.get(url, params={"symbol": "BTC", "convert": "BRL"}, headers=headers, timeout=10)
    r_brl.raise_for_status()
    price_brl = r_brl.json()["data"]["BTC"]["quote"]["BRL"]["price"]

    return price_usd, price_brl

def save_to_csv(price_usd, price_brl):
    filename = "btc_history.csv"
    file_exists = os.path.isfile(filename)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["datetime_utc", "price_usd", "price_brl"])
        writer.writerow([now, f"{price_usd:.2f}", f"{price_brl:.2f}"])
    return now

def generate_chart():
    if not os.path.isfile("btc_history.csv"):
        return
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

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

def check_variation(price_usd, price_brl):
    filename = "btc_history.csv"
    if not os.path.isfile(filename):
        return None
    df = pd.read_csv(filename)
    if df.empty:
        return None
    last_usd = float(df["price_usd"].iloc[-1])
    last_brl = float(df["price_brl"].iloc[-1])
    var_usd = abs(price_usd - last_usd) / last_usd * 100
    var_brl = abs(price_brl - last_brl) / last_brl * 100
    if var_usd >= VARIACAO_ALERTA or var_brl >= VARIACAO_ALERTA:
        return var_usd, var_brl
    return None

def should_send_regular(now_utc):
    """Verifica se o horário atual é um dos horários de notificação regular"""
    hora_min = now_utc[11:16]  # pega HH:MM
    return hora_min in NOTIF_HORARIOS

def main():
    try:
        price_usd, price_brl = get_btc_price()
        now = save_to_csv(price_usd, price_brl)
        generate_chart()

        # 1️⃣ Alertas imediatos por variação
        variation = check_variation(price_usd, price_brl)
        if variation:
            var_usd, var_brl = variation
            alert_text = (
                f"⚠️ Alerta de variação BTC!\n"
                f"Preço: 🇺🇸 ${price_usd:,.2f} | 🇧🇷 R${price_brl:,.2f}\n"
                f"Variação desde última cotação:\n"
                f"🇺🇸 {var_usd:.2f}% | 🇧🇷 {var_brl:.2f}%"
            )
            send_telegram(alert_text)

        # 2️⃣ Notificação regular 3x ao dia
        if should_send_regular(now):
            text = (
                f"💰 Bitcoin (BTC) - Cotação regular\n"
                f"🇺🇸 USD: ${price_usd:,.2f}\n"
                f"🇧🇷 BRL: R${price_brl:,.2f}"
            )
            send_telegram(text)

        print("Execução finalizada:", now)

    except Exception as e:
        error_msg = f"⚠️ Erro ao buscar cotação BTC: {e}"
        print(error_msg)
        try:
            send_telegram(error_msg)
        except:
            pass

if __name__ == "__main__":
    main()
