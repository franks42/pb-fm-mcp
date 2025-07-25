from typing import Any, Union
from decimal import Decimal

# Base Currency in Trading Pairs: In a crypto trading pair like BTC/USDT, 
# the base currency (BTC in this example) is the asset being valued, 
# and the quote currency (USDT) expresses its value. 
# The base currency is the one you are buying or selling, 
# while the quote currency indicates its price. 

assets_denoms = [
		{"denom": "nhash", "base_denom": "nhash", "conv": 1, "unit_denom": "hash", "symbol": "HASH"},
		{"denom": "hash", "base_denom": "nhash", "conv": 1000000000, "unit_denom": "hash", "symbol": "HASH"},
		
		{"denom": "neth.figure.se", "base_denom": "neth", "conv": 1, "unit_denom": "eth", "symbol": "ETH"},
		{"denom": "neth", "base_denom": "neth", "conv": 1, "unit_denom": "eth", "symbol": "ETH"},
		{"denom": "eth", "base_denom": "neth", "conv": 1000000000, "unit_denom": "eth", "symbol": "ETH"},
		
		{"denom": "nsol.figure.se", "base_denom": "nsol", "conv": 1, "unit_denom": "sol", "symbol": "SOL"},
		{"denom": "nsol", "base_denom": "nsol", "conv": 1, "unit_denom": "sol", "symbol": "SOL"},
		{"denom": "sol", "base_denom": "nsol", "conv": 1000000000, "unit_denom": "sol", "symbol": "SOL"},
	
		{"denom": "nbtc.figure.se", "base_denom": "nbtc", "conv": 1, "unit_denom": "btc", "symbol": "BTC"},
		{"denom": "nbtc", "base_denom": "nbtc", "conv": 1, "unit_denom": "btc", "symbol": "BTC"},
		{"denom": "btc", "base_denom": "nbtc", "conv": 1000000000, "unit_denom": "btc", "symbol": "BTC"},
	
		{"denom": "nlink.figure.se", "base_denom": "nlink", "conv": 1, "unit_denom": "link", "symbol": "LINK"},
		{"denom": "nlink", "base_denom": "nlink", "conv": 1, "unit_denom": "link", "symbol": "LINK"},
		{"denom": "link", "base_denom": "nlink", "conv": 1000000000, "unit_denom": "link", "symbol": "LINK"},
	
		{"denom": "nuni.figure.se", "base_denom": "nuni", "conv": 1, "unit_denom": "uni", "symbol": "UNI"},
		{"denom": "nuni", "base_denom": "nuni", "conv": 1, "unit_denom": "uni", "symbol": "UNI"},
		{"denom": "uni", "base_denom": "nuni", "conv": 1000000000, "unit_denom": "uni", "symbol": "UNI"},
	
		{"denom": "xrp", "base_denom": "uxrp", "conv": 1000000, "unit_denom": "xrp", "symbol": "XRP"},
		{"denom": "uxrp", "base_denom": "uxrp", "conv": 1, "unit_denom": "xrp", "symbol": "XRP"},
		{"denom": "uxrp.figure.se", "base_denom": "uxrp", "conv": 1, "unit_denom": "xrp", "symbol": "XRP"},
		
		{"denom": "usd", "base_denom": "uusd", "conv": 1000000, "unit_denom": "usd", "symbol": "USD"},
		{"denom": "uusd", "base_denom": "uusd", "conv": 1, "unit_denom": "usd", "symbol": "USD"},
		{"denom": "uusd.trading", "base_denom": "uusd", "conv": 1, "unit_denom": "usd", "symbol": "USD"},
		
		{"denom": "usdc", "base_denom": "uusdc", "conv": 1000000, "unit_denom": "usdc", "symbol": "USDC"},
		{"denom": "uusdc", "base_denom": "uusdc", "conv": 1, "unit_denom": "usdc", "symbol": "USDC"},
		{"denom": "uusdc.trading", "base_denom": "uusdc", "conv": 1, "unit_denom": "usdc", "symbol": "USDC"},
	
		{"denom": "usdt", "base_denom": "uusdt", "conv": 1000000, "unit_denom": "usdt", "symbol": "USDT"},
		{"denom": "uusdt", "base_denom": "uusdt", "conv": 1, "unit_denom": "usdt", "symbol": "USDT"},
		{"denom": "uusdt.trading", "base_denom": "uusdt", "conv": 1, "unit_denom": "usdt", "symbol": "USDT"},
	
		{"denom": "uylds.fcc", "base_denom": "uylds", "conv": 1, "unit_denom": "ylds", "symbol": "YLDS"},
		{"denom": "uylds", "base_denom": "uylds", "conv": 1, "unit_denom": "ylds", "symbol": "YLDS"},
		{"denom": "ylds", "base_denom": "uylds", "conv": 1000000, "unit_denom": "ylds", "symbol": "YLDS"},
		
	]

def amt_base_denom(amt_denom: Any) -> Any:
	"""for an amount-denom, like {"amount": 123, "denom": "hash"},
		the function converts the amount of the equivalent base denom according to the assets_denoms table,
		and will return: {"amount": 123000000000, "denom": "nhash"}
		if it does not recognize the denom, it will return the amount-denom unchanged.
	"""
	for asset_denom in assets_denoms:
		if amt_denom["denom"] == asset_denom["denom"]:
			return {"amount": int(Decimal(amt_denom["amount"]) * asset_denom["conv"]), "denom": asset_denom["base_denom"]}
	return amt_denom


if __name__ == "__main__":
	
	print(amt_base_denom({"amount": 10, "denom": "usd"}))	
	
	print(amt_base_denom({"amount": "10", "denom": "uusdc.trading"}))
	print(amt_base_denom({"amount": 10, "denom": "btc"}))
	print(amt_base_denom({"amount": "1234.5678912345", "denom": "btc.jaja"}))
	
	
	
	