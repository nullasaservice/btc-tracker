#!/usr/bin/env python3
import os
import json
import time
import hmac
import hashlib
import urllib.request
import argparse


CONFIG_FILE = "config.json"

# FIXED USD → EUR rate when using --assume-price
EUR_RATE = 0.92   # <-- change this whenever you want


# -------------------------------
#   Fetch BTC price (USD + EUR)
# -------------------------------
def fetch_btc_price():
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd,eur"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data["bitcoin"]["usd"], data["bitcoin"]["eur"]
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None, None


# -------------------------------
#  Fetch BTC address balance
# -------------------------------
def fetch_btc_address_balance(address):
    url = f"https://blockchain.info/q/addressbalance/{address}?confirmations=6"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            satoshis = int(r.read().decode())
            return satoshis / 1e8
    except Exception as e:
        print(f"Error fetching balance for {address}: {e}")
        return 0.0


# -------------------------------
#   Binance Spot BTC balance
# -------------------------------
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


# -------------------------------
#      CONFIG SETUP
# -------------------------------
def setup_config():
    print("=== First-Time Setup ===")

    addresses = []
    print("\nEnter your BTC addresses (empty input to finish):")
    while True:
        addr = input("BTC Address: ").strip()
        if not addr:
            break
        addresses.append(addr)

    api_key = input("\nBinance API Key: ").strip()
    api_secret = input("Binance API Secret: ").strip()

    config = {
        "btc_addresses": addresses,
        "binance_api_key": api_key,
        "binance_api_secret": api_secret
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print("\n✔ Config saved!\n")
    return config


# -------------------------------
#            MAIN
# -------------------------------
def main():
    parser = argparse.ArgumentParser(description="BTC Tracker CLI")
    parser.add_argument("--assume-price", type=float,
                        help="Assume a manual BTC price in USD")
    args = parser.parse_args()

    print("=== BTC Tracker ===\n")

    # Load config
    if not os.path.exists(CONFIG_FILE):
        config = setup_config()
    else:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

    addresses = config["btc_addresses"]
    api_key = config["binance_api_key"]
    api_secret = config["binance_api_secret"]

    # -----------------------------------------------------
    # PRICE HANDLING
    # -----------------------------------------------------
    if args.assume_price:
        price_usd = args.assume_price
        price_eur = price_usd * EUR_RATE

        print(f"Using mocked BTC price:")
        print(f"USD: {price_usd:.2f}")
        print(f"EUR: {price_eur:.2f}  (fixed EUR rate {EUR_RATE})\n")

    else:
        price_usd, price_eur = fetch_btc_price()
        if not price_usd:
            print("Failed to fetch BTC price. Exiting.")
            return

        print(f"BTC Price:  USD {price_usd:,.2f} | EUR {price_eur:,.2f}\n")

    # -----------------------------------------------------
    # BTC ADDRESSES
    # -----------------------------------------------------
    total_btc_addresses = 0
    print("=== BTC Address Balances ===")
    for addr in addresses:
        bal = fetch_btc_address_balance(addr)
        total_btc_addresses += bal
        print(f"{addr}: {bal:.8f} BTC  |  USD {bal * price_usd:.2f}  |  EUR {bal * price_eur:.2f}")

    # -----------------------------------------------------
    # BINANCE BALANCE
    # -----------------------------------------------------
    print("\n=== Binance BTC Spot Balance ===")
    spot_btc = fetch_binance_spot_balance(api_key, api_secret)
    print(f"Binance: {spot_btc:.8f} BTC  |  USD {spot_btc * price_usd:.2f}  |  EUR {spot_btc * price_eur:.2f}\n")

    # -----------------------------------------------------
    # TOTAL
    # -----------------------------------------------------
    total_btc = total_btc_addresses + spot_btc
    print("=== TOTAL BTC VALUE ===")
    print(f"TOTAL BTC: {total_btc:.8f}")
    print(f"TOTAL USD: {total_btc * price_usd:,.2f}")
    print(f"TOTAL EUR: {total_btc * price_eur:,.2f}")


if __name__ == "__main__":
    main()
