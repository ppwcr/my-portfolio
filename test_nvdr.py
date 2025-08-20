#!/usr/bin/env python3
import requests
import json

response = requests.get("http://localhost:8000/api/portfolio/dashboard?trade_date=2025-08-20")
data = response.json()

nvdr_count = sum(1 for stock in data['portfolio_stocks'] if stock.get('nvdr', 0) != 0)
short_count = sum(1 for stock in data['portfolio_stocks'] if stock.get('shortBaht', 0) != 0)

print(f"NVDR data: {nvdr_count} stocks")
print(f"Short Sales data: {short_count} stocks")
print(f"Total stocks: {len(data['portfolio_stocks'])}")

# Show a sample stock
if data['portfolio_stocks']:
    sample = data['portfolio_stocks'][0]
    print(f"Sample stock: {sample['symbol']} - NVDR: {sample.get('nvdr', 0)}, Short: {sample.get('shortBaht', 0)}")