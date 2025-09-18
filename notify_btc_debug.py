# notify_btc_debug.py
import os
import requests
from datetime import datetime, timezone, timedelta
import json
import time

# --- configurações ---
CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DRY_RUN = os.getenv("TELEGRAM_DEBUG_DRY_RUN", "0")  # se "1", não envia mensagens, só checa

CSV_FILE = "btc_history.csv"
PNG_FILE = "btc_chart.png"

# --- utilitários ---
def mask(s, left=6, right=4):
    if not s:
        return "<NÃO DEFINIDO>"
    s = str(s)
    if len(s) <= left + right + 3:
        return s
    return s[:left] + "..." + s[-right:]

def pretty_print_json(j):
    try:
        print(json.dumps(j, indent=2, ensure_ascii=False))
    except Exception:
        print(str(j))

# timezone helpers (fallback se zoneinfo não disponível)
try:
    from zoneinfo import ZoneInfo
    tz_sp = ZoneInfo("America/Sao_Paulo")
    tz_pvh = ZoneInfo("America/Porto_Velho")
except Exception:
    tz_sp = timezone(timedelta(hours=-3))
    tz_pvh = timezone(timedelta(hours=-4))

# --- verificações iniciais ---
def check_env():
    print("=== ENVIRONMENT ===")
    print("CMC_API_KEY:", mask(CMC_API_KEY))
    print("TELEGRAM_BOT_TOKEN:", mask(TELEGRAM_BOT_TOKEN))
    print("TELEGRAM_CHAT_ID:", TELEGRAM_CHAT_ID if TELEGRAM_CHAT_ID else "<NÃO DEFINIDO>")
    print("DRY_RUN:", DRY_RUN)
    print()

# --- horário / agendamento esperado ---
def show_times():
    now_utc = datetime.now(timezone.utc).replace(microsecond=0)
    now_sp = now_utc.astimezone(tz_sp)
    now_pvh = now_utc.astimezone(tz_pvh)
    print("=== HORÁRIOS ATUAIS ===")
    print("UTC:", now_utc.isoformat())
    print("São_Paulo:", now_sp.isoformat())
    print("Porto_Velho:", now_pvh.isoformat())
    print()

    # checar janelas de envio possíveis (várias convenções para garantir)
    def in_window(now, hours_list):
        return now.hour in hours_list and now.minute < 15

    print("=== Verificação de janelas de envio (first 15 min) ===")
    # a) configuração usada em algumas versões do script (UTC hours)
    print("Config A (UTC hours [12,16,20]):", in_window(now_utc, [12,16,20]))
    # b) configuração que representava 06h,13h,20h Cuiabá (NOTIF_HORARIOS = ['10:00','17:00','00:00'])
    print("Config B (Cuiabá->UTC ['10:00','17:00','00:00']):", in_window(now_utc, [10,17,0]))
    # c) se você esperava 06h/13h/20h BRT (Brasília UTC-3)
    print("Config C (Brasília->UTC [9,16,23]):", in_window(now_utc, [9,16,23]))
    print()

# --- chamadas para testar Telegram ---
def telegram_get(method, params=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.status_code, r.text, r
    except Exception as e:
        return None, f"Exception: {e}", None

def telegram_post_file(method, files=None, data=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    try:
        r = requests.post(url, files=files, data=data, timeout=20)
        return r.status_code, r.text, r
    except Exception as e:
        return None, f"Exception: {e}", None

def do_telegram_checks():
    print("=== TELEGRAM CHECKS ===")
    if not TELEGRAM_BOT_TOKEN:
        print("Token do Telegram não definido! Pare e verifique secrets.")
        return

    # 1) getMe
    status, text, resp = telegram_get("getMe")
    print("getMe status:", status)
    print("getMe response:")
    try:
        pretty_print_json(resp.json())
    except Exception:
        print(text)
    print()

    # 2) getChat (se chat_id definido)
    if TELEGRAM_CHAT_ID:
        status, text, resp = telegram_get("getChat", params={"chat_id": TELEGRAM_CHAT_ID})
        print("getChat status:", status)
        print("getChat response:")
        try:
            pretty_print_json(resp.json())
        except Exception:
            print(text)
        print()
    else:
        print("TELEGRAM_CHAT_ID não definido; getChat pulado.")
        print()

    # 3) getUpdates (útil para ver se o bot recebeu mensagens)
    status, text, resp = telegram_get("getUpdates")
    print("getUpdates status:", status)
    print("getUpdates (últimas):")
    try:
        j = resp.json()
        # imprimir só os últimos 5 updates para não poluir
        if "result" in j and isinstance(j["result"], list):
            print("Total updates:", len(j["result"]))
            pretty_print_json(j["result"][-5:])
        else:
            pretty_print_json(j)
    except Exception:
        print(text)
    print()

# --- tentativa de envio de teste ---
def try_send_test_message():
    if DRY_RUN == "1":
        print("DRY_RUN ativo – não será enviado test message.")
        return
    print("=== ENVIO DE TEST MESSAGE ===")
    text = f"[DEBUG TEST] Mensagem de teste automática. Hora UTC: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        print("sendMessage status:", r.status_code)
        try:
            pretty_print_json(r.json())
        except Exception:
            print(r.text)
    except Exception as e:
        print("Erro ao chamar sendMessage:", e)
    print()

def try_send_test_photo():
    if DRY_RUN == "1":
        print("DRY_RUN ativo – não será enviado photo.")
        return
    print("=== ENVIO DE TEST PHOTO (se existir) ===")
    if not os.path.isfile(PNG_FILE):
        print("Arquivo PNG não existe:", PNG_FILE)
        return
    try:
        with open(PNG_FILE, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": "[DEBUG TEST] Gráfico BTC (debug)"}
            status, text, resp = telegram_post_file("sendPhoto", files=files, data=data)
            print("sendPhoto status:", status)
            try:
                pretty_print_json(resp.json())
            except Exception:
                print(text)
    except Exception as e:
        print("Erro ao abrir/enviar PNG:", e)
    print()

# --- checar arquivo png/csv e timestamps ---
def check_files():
    print("=== ARQUIVOS (CSV/PNG) ===")
    if os.path.isfile(CSV_FILE):
        ts = datetime.fromtimestamp(os.path.getmtime(CSV_FILE), timezone.utc).replace(microsecond=0)
        size = os.path.getsize(CSV_FILE)
        print(f"{CSV_FILE}: existe, tamanho={size} bytes, mtime(UTC)={ts.isoformat()}")
    else:
        print(f"{CSV_FILE}: NÃO EXISTE")

    if os.path.isfile(PNG_FILE):
        ts = datetime.fromtimestamp(os.path.getmtime(PNG_FILE), timezone.utc).replace(microsecond=0)
        size = os.path.getsize(PNG_FILE)
        print(f"{PNG_FILE}: existe, tamanho={size} bytes, mtime(UTC)={ts.isoformat()}")
    else:
        print(f"{PNG_FILE}: NÃO EXISTE")
    print()

# --- opcional: checar CoinMarketCap (pequeno teste) ---
def check_coinmarketcap():
    print("=== TESTE RÁPIDO COINMARKETCAP (HEAD) ===")
    if not CMC_API_KEY:
        print("CMC_API_KEY não definido; pulando teste CMC.")
        return
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    try:
        r = requests.get(url, headers=headers, params={"symbol":"BTC","convert":"USD"}, timeout=10)
        print("CMC status:", r.status_code)
        try:
            pretty_print_json(r.json() if r.status_code == 200 else r.text)
        except Exception:
            print(r.text)
    except Exception as e:
        print("Erro teste CMC:", e)
    print()

# --- execução principal ---
def main():
    print("\n=== START DEBUG notify_btc_debug.py ===\n")
    check_env()
    show_times()
    check_files()
    check_coinmarketcap()
    do_telegram_checks()
    # enviar testes (se DRY_RUN != "1")
    try_send_test_message()
    try_send_test_photo()
    print("\n=== END DEBUG ===\n")

if __name__ == "__main__":
    main()
