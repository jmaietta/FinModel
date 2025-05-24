"""
Data adapter module for integrating multiple financial data sources.

This module provides adapters for different financial data sources,
allowing the parser to work with SEC EDGAR, third-party APIs, or local files.
"""
import os
import logging
import json
import requests
from typing import Dict, List, Any
from datetime import datetime
from abc import ABC, abstractmethod


class DataAdapter(ABC):
    """Abstract base class for data adapters."""
    
    @abstractmethod
    def get_income_statement(self, 
                             ticker: str, 
                             period: str = 'quarterly',
                             limit: int = 20) -> Dict[str, Any]:
        """Get income statement data for a company.
        """
        pass


class PolygonAdapter(DataAdapter):
    """Adapter for Polygon.io API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, 
                             ticker: str, 
                             period: str = 'quarterly',
                             limit: int = 20) -> Dict[str, Any]:
        timeframe = 'quarterly' if period == 'quarterly' else 'annual'
        try:
            url = (
                f"{self.base_url}/v2/reference/financials"
                f"?ticker={ticker}"
                f"&statement=ic"
                f"&timeframe={timeframe}"
                f"&limit={limit}"
                f"&apiKey={self.api_key}"
            )
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {'periods': data.get('results', [])}
        except Exception as e:
            self.logger.error(f"Polygon failed for {ticker}: {e}")
            return {}


class SimFinAdapter(DataAdapter):
    """Adapter for SimFin API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.simfin.com"
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, 
                             ticker: str, 
                             period: str = 'quarterly',
                             limit: int = 20) -> Dict[str, Any]:
        stmt = 'ic'
        per = 'quarterly' if period == 'quarterly' else 'annual'
        try:
            url = (
                f"{self.base_url}/v2/companies/statements"
                f"?ticker={ticker}"
                f"&statement={stmt}"
                f"&statement_period={per}"
                f"&limit={limit}"
                f"&api-key={self.api_key}"
            )
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {'periods': data.get('statements', [])}
        except Exception as e:
            self.logger.error(f"SimFin failed for {ticker}: {e}")
            return {}


class AlphaVantageAdapter(DataAdapter):
    """Adapter for Alpha Vantage API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, 
                             ticker: str, 
                             period: str = 'quarterly',
                             limit: int = 20) -> Dict[str, Any]:
        try:
            params = {
                'function': 'INCOME_STATEMENT',
                'symbol': ticker,
                'apikey': self.api_key
            }
            resp = requests.get(self.base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            key = 'quarterlyReports' if period == 'quarterly' else 'annualReports'
            periods = data.get(key, [])[:limit]
            return {'periods': periods}
        except Exception as e:
            self.logger.error(f"AlphaVantage failed for {ticker}: {e}")
            return {}


class FinnhubAdapter(DataAdapter):
    """Adapter for Finnhub API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, 
                             ticker: str, 
                             period: str = 'quarterly',
                             limit: int = 20) -> Dict[str, Any]:
        freq = 'quarterly' if period == 'quarterly' else 'annual'
        try:
            url = (
                f"{self.base_url}/stock/financials-reported"
                f"?symbol={ticker}"
                f"&statement=ic"
                f"&freq={freq}"
                f"&token={self.api_key}"
            )
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return {'periods': data.get('data', [])[:limit]}
        except Exception as e:
            self.logger.error(f"Finnhub failed for {ticker}: {e}")
            return {}


class LocalFileAdapter(DataAdapter):
    """Adapter for local file data."""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        os.makedirs(data_dir, exist_ok=True)
    
    def get_income_statement(self, 
                             ticker: str, 
                             period: str = 'quarterly',
                             limit: int = 20) -> Dict[str, Any]:
        file_path = os.path.join(self.data_dir, f"{ticker}_income_statement.json")
        if not os.path.exists(file_path):
            self.logger.warning(f"Local file not found for {ticker}")
            return {}
        try:
            with open(file_path) as f:
                data = json.load(f)
            periods = data.get('periods', {})
            # Filter and limit
            filtered = {d: v for d, v in periods.items() if v.get('period_type', '') == period}
            items = dict(list(filtered.items())[:limit])
            return {'periods': items}
        except Exception as e:
            self.logger.error(f"Local file read failed for {ticker}: {e}")
            return {}


class AdapterFactory:
    """Factory for creating data adapters."""
    @staticmethod
    def create_adapter(adapter_type: str, config: Dict[str, Any]) -> DataAdapter:
        if adapter_type == 'polygon':
            return PolygonAdapter(config.get('api_key', ''))
        elif adapter_type == 'simfin':
            return SimFinAdapter(config.get('api_key', ''))
        elif adapter_type == 'alphavantage':
            return AlphaVantageAdapter(config.get('api_key', ''))
        elif adapter_type == 'finnhub':
            return FinnhubAdapter(config.get('api_key', ''))
        elif adapter_type == 'local':
            return LocalFileAdapter(config.get('data_dir', './data'))
        else:
            raise ValueError(f"Unsupported adapter type: {adapter_type}")
