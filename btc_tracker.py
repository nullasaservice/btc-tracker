#!/usr/bin/env python3
import os
import json
import time
import hmac
import hashlib
import urllib.request
import argparse
import base64
import getpass

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.enc")
EUR_RATE = 0.92


# =====================================================
#                ENCRYPTION HELPERS
# =====================================================

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_config(data: dict, password: str):
    salt = os.urandom(16)
    key = derive_key(password, salt)
    f = Fernet(key)
    encrypted = f.encrypt(json.dumps(data).encode())

    with open(CONFIG_FILE, "wb") as f_out:
        f_out.write(salt + encrypted)


def decrypt_config(password: str) -> dict:
    with open(CONFIG_FILE, "rb") as f:
        raw = f.read()

    salt = raw[:16]
    encrypted = raw[16:]

    key = derive_key(password, salt)
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted)

    return json.loads(decrypted.decode())


# =====================================================
#                PRICE FETCHING
# =====================================================

def fetch_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,eur"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data["bitcoin"]["usd"], data["bitcoin"]["eur"]
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None, None


# =====================================================
#                BTC BALANCES
# =====================================================

def fetch_btc_address_balance(address):
    url = f"https://blockchain.info/q/addressbalance/{address}?confirmations=6"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            satoshis = int(r.read().decode())
            return satoshis / 1e8
    except Exception as e:
        print(f"Error fetching balance for {address}: {e}")
        return 0.0


def fetch_binance_spot_balance(api_key, api_secret):
    base = "https://api.binance.com"
    endpoint = "/api/v3/account"

    ts = int(time.time() * 1000)
    query = f"timestamp={ts}"

    signature = hmac.new(
        api_secret.encode(),
        query.encode(),
        hashlib.sha256
    ).hexdigest()

    url = f"{base}{endpoint}?{query}&signature={signature}"
    req = urllib.request.Request(url)
    req.add_header("X-MBX-APIKEY", api_key)

    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            for asset in data["balances"]:
                if asset["asset"] == "BTC":
                    return float(asset["free"]) + float(asset["locked"])
            return 0.0
    except Exception as e:
        print(f"Error fetching Binance balance: {e}")
        return 0.0


# =====================================================
#                CONFIG SETUP
# =====================================================

def setup_config():
    print("=== First-Time Setup ===")

    addresses = []
    while True:
        addr = input("BTC Address (empty to finish): ").strip()
        if not addr:
            break
        addresses.append(addr)

    api_key = input("Binance API Key: ").strip()
    api_secret = input("Binance API Secret: ").strip()

    password = getpass.getpass("Create encryption password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.")
        exit(1)

    config = {
        "btc_addresses": addresses,
        "binance_api_key": api_key,
        "binance_api_secret": api_secret
    }

    encrypt_config(config, password)
    print("✔ Config encrypted and saved.")
    return config


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return setup_config()

    password = getpass.getpass("Enter config password: ")
    try:
        return decrypt_config(password)
    except Exception:
        print("Invalid password or corrupted config.")
        exit(1)


# =====================================================
#                     MAIN
# =====================================================

def main():
    parser = argparse.ArgumentParser(description="BTC Tracker CLI")
    parser.add_argument("--assume-price", type=float, help="Mock BTC price in USD")
    parser.add_argument("--show-config", action="store_true",
                        help="Decrypt and display config")
    args = parser.parse_args()

    config = load_config()

    if args.show_config:
        print(json.dumps(config, indent=2))
        return

    print("\n=== BTC Tracker ===\n")

    # PRICE
    if args.assume_price:
        price_usd = args.assume_price
        price_eur = price_usd * EUR_RATE
        print(f"Using mocked BTC price:")
        print(f"USD: {price_usd:.2f}")
        print(f"EUR: {price_eur:.2f}\n")
    else:
        price_usd, price_eur = fetch_btc_price()
        if not price_usd:
            print("Failed to fetch BTC price.")
            return

        print(f"BTC Price: USD {price_usd:,.2f} | EUR {price_eur:,.2f}\n")

    total_btc_addresses = 0

    print("=== BTC Address Balances ===")
    for addr in config["btc_addresses"]:
        bal = fetch_btc_address_balance(addr)
        total_btc_addresses += bal
        print(f"{addr}: {bal:.8f} BTC | USD {bal * price_usd:.2f} | EUR {bal * price_eur:.2f}")

    print("\n=== Binance BTC Spot Balance ===")
    spot_btc = fetch_binance_spot_balance(
        config["binance_api_key"],
        config["binance_api_secret"]
    )

    print(f"Binance: {spot_btc:.8f} BTC | USD {spot_btc * price_usd:.2f} | EUR {spot_btc * price_eur:.2f}\n")

    total_btc = total_btc_addresses + spot_btc

    print("=== TOTAL BTC VALUE ===")
    print(f"TOTAL BTC: {total_btc:.8f}")
    print(f"TOTAL USD: {total_btc * price_usd:,.2f}")
    print(f"TOTAL EUR: {total_btc * price_eur:,.2f}")


if __name__ == "__main__":
    main()
