"""
Provider selection module now using only PolygonAdapter.
"""
import logging
#from src.adapter.data_adapter import PolygonAdapter

class ProviderSelector:
    """Provider selector simplified to use only Polygon."""
    def __init__(self, api_keys: dict):
        self.api_key = api_keys.get('polygon', '')
        self.adapter = PolygonAdapter(self.api_key)
        self.logger = logging.getLogger(__name__)

    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch income statement via Polygon only."""
        self.logger.info(f"Fetching income statement for {ticker} via Polygon")
        return self.adapter.get_income_statement(ticker, period, limit)
