import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timezone

CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CSV_FILE = "btc_history.csv"
PNG_FILE = "btc_chart.png"

# -------------------------------
# Funções de envio ao Telegram
# -------------------------------
def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    r = requests.post(url, json=payload, timeout=10)
    print("DEBUG send_telegram status:", r.status_code, r.text)
    r.raise_for_status()
    return r.json()

def send_telegram_photo(photo_path: str, caption: str = ""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    if not os.path.isfile(photo_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {photo_path}")
    with open(photo_path, "rb") as photo:
        files = {"photo": photo}
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
        r = requests.post(url, files=files, data=data, timeout=10)
        print("DEBUG send_telegram_photo status:", r.status_code, r.text)
        r.raise_for_status()
        return r.json()

# -------------------------------
# Cotação CoinMarketCap
# -------------------------------
def get_btc_price():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

    prices = {}
    for currency in ["USD", "BRL"]:
        params = {"symbol": "BTC", "convert": currency}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"DEBUG CoinMarketCap status {currency}:", r.status_code)
        r.raise_for_status()
        data = r.json()["data"]["BTC"]["quote"][currency]["price"]
        prices[currency] = data

    return prices["USD"], prices["BRL"]

# -------------------------------
# Histórico CSV + Gráfico
# -------------------------------
def save_price_to_csv(price_usd, price_brl):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    row = {"datetime_utc": now, "price_usd": price_usd, "price_brl": price_brl}
    df = pd.DataFrame([row])
    if not os.path.isfile(CSV_FILE):
        df.to_csv(CSV_FILE, index=False)
    else:
        df.to_csv(CSV_FILE, mode="a", header=False, index=False)
    print("DEBUG CSV atualizado:", row)
    return now

def generate_chart():
    if not os.path.isfile(CSV_FILE):
        print("DEBUG Nenhum CSV encontrado para gerar gráfico.")
        return False
    df = pd.read_csv(CSV_FILE, parse_dates=["datetime_utc"])
    if df.empty:
        print("DEBUG CSV vazio, não gera gráfico.")
        return False

    plt.figure(figsize=(10, 5))
    plt.plot(df["datetime_utc"], df["price_usd"], label="USD")
    plt.plot(df["datetime_utc"], df["price_brl"], label="BRL")
    plt.title("Histórico Bitcoin")
    plt.xlabel("Data (UTC)")
    plt.ylabel("Preço")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(PNG_FILE)
    plt.close()
    print("DEBUG Gráfico gerado:", PNG_FILE)
    return True

# -------------------------------
# Alertas e notificações
# -------------------------------
def check_variation(price_usd, price_brl, threshold=0.05):
    if not os.path.isfile(CSV_FILE):
        return None
    df = pd.read_csv(CSV_FILE)
    if df.shape[0] < 2:
        return None
    last_usd = df.iloc[-2]["price_usd"]
    variation_usd = (price_usd - last_usd) / last_usd
    if abs(variation_usd) >= threshold:
        return variation_usd
    return None

def should_send_regular(now):
    # Notifica 3x ao dia em UTC → 12h, 16h, 20h
    return now.hour in [12, 16, 20] and now.minute < 15

# -------------------------------
# Execução principal
# -------------------------------
def main():
    try:
        print("DEBUG Iniciando script BTC...")

        price_usd, price_brl = get_btc_price()
        now = save_price_to_csv(price_usd, price_brl)
        chart_ok = generate_chart()

        # Verificação de variação
        variation = check_variation(price_usd, price_brl)
        if variation:
            pct = variation * 100
            alert_text = (
                f"🚨 ALERTA: BTC variação {pct:+.2f}%\n"
                f"🇺🇸 USD: ${price_usd:,.2f}\n"
                f"🇧🇷 BRL: R${price_brl:,.2f}"
            )
            send_telegram(alert_text)

        # Notificações regulares
        print("DEBUG horário UTC:", now)
        print("DEBUG should_send_regular:", should_send_regular(now))

        if should_send_regular(now) and chart_ok:
            caption = (
                f"💰 Bitcoin (BTC) - Cotação regular\n"
                f"🇺🇸 USD: ${price_usd:,.2f}\n"
                f"🇧🇷 BRL: R${price_brl:,.2f}"
            )
            try:
                send_telegram_photo(PNG_FILE, caption=caption)
                print("DEBUG Foto enviada com sucesso.")
            except Exception as e:
                print("DEBUG Erro ao enviar foto:", e)
                send_telegram(f"⚠️ Erro ao enviar foto: {e}")

    except Exception as e:
        print("DEBUG Erro geral:", e)
        send_telegram(f"⚠️ Erro no bot BTC: {e}")

if __name__ == "__main__":
    main()
