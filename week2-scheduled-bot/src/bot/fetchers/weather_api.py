"""Weather API fetcher using wttr.in (no API key required)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    city: str
    temperature_c: float
    condition: str
    humidity: int
    wind_kph: float


class WeatherFetcher:
    """Fetch weather data from wttr.in (free, no API key)."""

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

    async def get_forecast(self, city: str) -> WeatherData:
        """
        Get current weather for a city.
        
        Uses wttr.in JSON API (no key required).
        Example: https://wttr.in/London?format=j1
        """
        if not self.session:
            raise RuntimeError("WeatherFetcher must be used as async context manager")

        url = f"https://wttr.in/{city}?format=j1"
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    logger.error(f"Weather API error: {resp.status}")
                    raise Exception(f"Weather API returned {resp.status}")
                
                data = await resp.json()
                current = data["current_condition"][0]
                
                return WeatherData(
                    city=city,
                    temperature_c=float(current["temp_C"]),
                    condition=current["weatherDesc"][0]["value"],
                    humidity=int(current["humidity"]),
                    wind_kph=float(current["windspeedKmph"]),
                )
        except Exception as e:
            logger.exception(f"Failed to fetch weather for {city}")
            raise


def format_weather_report(weather: WeatherData) -> str:
    """Format weather data as a user-friendly message."""
    emoji = _weather_emoji(weather.condition)
    return (
        f"{emoji} **{weather.city}**\n"
        f"🌡️ {weather.temperature_c}°C\n"
        f"☁️ {weather.condition}\n"
        f"💧 Humidity: {weather.humidity}%\n"
        f"💨 Wind: {weather.wind_kph} km/h"
    )


def _weather_emoji(condition: str) -> str:
    """Map weather condition to emoji."""
    condition_lower = condition.lower()
    if "clear" in condition_lower or "sunny" in condition_lower:
        return "☀️"
    elif "cloud" in condition_lower:
        return "☁️"
    elif "rain" in condition_lower:
        return "🌧️"
    elif "snow" in condition_lower:
        return "❄️"
    elif "storm" in condition_lower or "thunder" in condition_lower:
        return "⛈️"
    else:
        return "🌤️"
