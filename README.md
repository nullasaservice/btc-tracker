# BTC Tracker CLI

BTC Tracker CLI is a lightweight Python command-line tool designed to:

- Track BTC balances from:
  - Multiple Bitcoin wallet addresses  
  - A Binance Spot account  
- Fetch current BTC prices in USD and EUR  
- Optionally use a mocked BTC price via `--assume-price`  
- Store configuration locally encrypted in `config.enc`

---

## Features

### BTC Prices
Fetches real-time BTC price from CoinGecko:

- BTC → USD  
- BTC → EUR  

A custom BTC price can be set using:

```
--assume-price X
```

The EUR value is automatically calculated using a fixed conversion rate defined in the script:

```python
EUR_RATE = 0.92
```

Configuration settings can also be exported using:
```
--show-config
```

---

### BTC Address Balances
For each BTC address provided, the script retrieves the balance from Blockchain.com:

```
https://blockchain.info/q/addressbalance/<address>
```

Balances are displayed in BTC, USD, and EUR.

---

### Binance Spot BTC Balance
Tracks BTC balance on a Binance Spot account:

- Requires API Key and Secret (stored in `config.json`)  
- Only reads BTC balance; does not perform trading or withdrawals  

---

## Installation

1. Clone or download the script:

```
git clone <repo-url>
cd btc-tracker
```

2. (Optional) Create a virtual environment:

```
python3 -m venv venv
source venv/bin/activate
```

3. Run the script:

```
python3 btc_tracker.py
```

No additional dependencies are required — the script uses only standard Python libraries.

---

## First-Time Setup

On first execution, the CLI prompts for:

1. BTC wallet addresses  
2. Binance API Key  
3. Binance API Secret  

The information is saved in:

```
config.json
```

---

## Usage

### Run with live BTC prices

```
python3 btc_tracker.py
```

### Run with a mocked BTC price

```
python3 btc_tracker.py --assume-price 95000
```

- BTC price = $95,000 USD  
- BTC price = €87,400 EUR (using the fixed EUR rate)

Example output:

```
=== BTC Tracker ===

BTC Price: USD 95,000.00 | EUR 87,400.00

=== BTC Address Balances ===
1BitcoinAddress...: 0.12345678 BTC | USD 11728.39 | EUR 9956.99
...

=== Binance BTC Spot Balance ===
Binance: 0.50000000 BTC | USD 47500.00 | EUR 43700.00

=== TOTAL BTC VALUE ===
TOTAL BTC: 0.62345678
TOTAL USD: 59228.39
TOTAL EUR: 53656.99
```

---

## Configuration

`config.json` stores:

```json
{
  "btc_addresses": ["addr1", "addr2", ...],
  "binance_api_key": "YOUR_KEY",
  "binance_api_secret": "YOUR_SECRET"
}
```

Deleting this file triggers the setup process on next execution.

---

## Security

- API keys are stored unencrypted.  
- Binance keys should be **read-only**.  
- An encrypted version of the configuration can be implemented for enhanced security.

---

## Future Improvements

Potential enhancements include:

- Compact summary mode
- Hiding BTC addresses in output

BTC Tracker CLI provides a simple and effective way to monitor BTC holdings and current prices from multiple sources.
