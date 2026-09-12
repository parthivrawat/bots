"""Crypto price API fetcher using CoinGecko (free, no API key for basic use)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class CryptoPrice:
    symbol: str
    price_usd: float
    change_24h: float


class CryptoFetcher:
    """Fetch crypto prices from CoinGecko API (free tier, no key required)."""

    BASE_URL = "https://api.coingecko.com/api/v3"
    
    # Map common symbols to CoinGecko IDs
    SYMBOL_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "USDT": "tether",
        "BNB": "binancecoin",
        "SOL": "solana",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
    }

    def __init__(self, session: aiohttp.ClientSession | None = None):
        self.session = session
        self._own_session = session is None

    async def __aenter__(self):
        if self._own_session:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self._own_session and self.session:
            await self.session.close()

    async def get_price(self, symbol: str) -> float:
        """
        Get current price for a crypto symbol.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Current price in USD
        """
        if not self.session:
            raise RuntimeError("CryptoFetcher must be used as async context manager")

        coin_id = self.SYMBOL_MAP.get(symbol.upper())
        if not coin_id:
            raise ValueError(f"Unknown crypto symbol: {symbol}")

        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }

        try:
            async with self.session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    logger.error(f"CoinGecko API error: {resp.status}")
                    raise Exception(f"CoinGecko API returned {resp.status}")

                data = await resp.json()
                if coin_id not in data:
                    raise Exception(f"No data for {symbol}")

                return data[coin_id]["usd"]

        except Exception as e:
            logger.exception(f"Failed to fetch price for {symbol}")
            raise

    async def get_price_detailed(self, symbol: str) -> CryptoPrice:
        """Get detailed price info including 24h change."""
        if not self.session:
            raise RuntimeError("CryptoFetcher must be used as async context manager")

        coin_id = self.SYMBOL_MAP.get(symbol.upper())
        if not coin_id:
            raise ValueError(f"Unknown crypto symbol: {symbol}")

        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }

        try:
            async with self.session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    logger.error(f"CoinGecko API error: {resp.status}")
                    raise Exception(f"CoinGecko API returned {resp.status}")

                data = await resp.json()
                if coin_id not in data:
                    raise Exception(f"No data for {symbol}")

                coin_data = data[coin_id]
                return CryptoPrice(
                    symbol=symbol.upper(),
                    price_usd=coin_data["usd"],
                    change_24h=coin_data.get("usd_24h_change", 0.0),
                )

        except Exception as e:
            logger.exception(f"Failed to fetch price for {symbol}")
            raise


def format_price_alert(symbol: str, price: float, condition: str, threshold: float) -> str:
    """Format a price alert message."""
    emoji = "🚀" if condition == "above" else "📉"
    return (
        f"{emoji} **Price Alert: {symbol}**\n"
        f"Current price: ${price:,.2f}\n"
        f"Threshold: ${threshold:,.2f} ({condition})\n"
        f"Alert triggered!"
    )
