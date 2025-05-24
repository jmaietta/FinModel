"""
Data adapter module for financial data providers.
"""
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class PolygonAdapter:
    """Adapter for Polygon.io API to fetch financial data."""
    
    def __init__(self, api_key: str):
        """Initialize Polygon adapter with API key."""
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.logger = logging.getLogger(__name__)
        
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make HTTP request to Polygon API."""
        try:
            params['apikey'] = self.api_key
            url = f"{self.base_url}{endpoint}"
            
            self.logger.info(f"Making request to: {url}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return None
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> List[Dict]:
        """
        Fetch income statement data from Polygon.
        
        Args:
            ticker: Stock ticker symbol
            period: 'quarterly' or 'annual'
            limit: Number of periods to fetch
            
        Returns:
            List of income statement data dictionaries
        """
        try:
            # Map period parameter to Polygon's expected values
            timeframe = 'quarterly' if period.lower() == 'quarterly' else 'annual'
            
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': timeframe,
                'limit': limit,
                'filing_date.gte': '2020-01-01'  # Get data from 2020 onwards
            }
            
            self.logger.info(f"Fetching {period} income statement for {ticker}")
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                self.logger.warning(f"No income statement data found for {ticker}")
                return []
            
            # Process and format the response
            formatted_data = []
            for result in data.get('results', []):
                if 'financials' in result and 'income_statement' in result['financials']:
                    income_stmt = result['financials']['income_statement']
                    
                    # Extract key financial metrics
                    formatted_item = {
                        'ticker': ticker.upper(),
                        'period_end_date': result.get('end_date', ''),
                        'filing_date': result.get('filing_date', ''),
                        'timeframe': result.get('timeframe', ''),
                        'revenue': income_stmt.get('revenues', {}).get('value', 0),
                        'cost_of_revenue': income_stmt.get('cost_of_revenue', {}).get('value', 0),
                        'gross_profit': income_stmt.get('gross_profit', {}).get('value', 0),
                        'operating_expenses': income_stmt.get('operating_expenses', {}).get('value', 0),
                        'operating_income': income_stmt.get('operating_income_loss', {}).get('value', 0),
                        'net_income': income_stmt.get('net_income_loss', {}).get('value', 0),
                        'basic_eps': income_stmt.get('basic_earnings_per_share', {}).get('value', 0),
                        'diluted_eps': income_stmt.get('diluted_earnings_per_share', {}).get('value', 0),
                    }
                    formatted_data.append(formatted_item)
            
            self.logger.info(f"Successfully fetched {len(formatted_data)} income statement records for {ticker}")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error fetching income statement for {ticker}: {str(e)}")
            return []
    
    def get_balance_sheet(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> List[Dict]:
        """
        Fetch balance sheet data from Polygon.
        
        Args:
            ticker: Stock ticker symbol
            period: 'quarterly' or 'annual'
            limit: Number of periods to fetch
            
        Returns:
            List of balance sheet data dictionaries
        """
        try:
            timeframe = 'quarterly' if period.lower() == 'quarterly' else 'annual'
            
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': timeframe,
                'limit': limit,
                'filing_date.gte': '2020-01-01'
            }
            
            self.logger.info(f"Fetching {period} balance sheet for {ticker}")
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                self.logger.warning(f"No balance sheet data found for {ticker}")
                return []
            
            formatted_data = []
            for result in data.get('results', []):
                if 'financials' in result and 'balance_sheet' in result['financials']:
                    balance_sheet = result['financials']['balance_sheet']
                    
                    formatted_item = {
                        'ticker': ticker.upper(),
                        'period_end_date': result.get('end_date', ''),
                        'filing_date': result.get('filing_date', ''),
                        'timeframe': result.get('timeframe', ''),
                        'total_assets': balance_sheet.get('assets', {}).get('value', 0),
                        'current_assets': balance_sheet.get('current_assets', {}).get('value', 0),
                        'total_liabilities': balance_sheet.get('liabilities', {}).get('value', 0),
                        'current_liabilities': balance_sheet.get('current_liabilities', {}).get('value', 0),
                        'total_equity': balance_sheet.get('equity', {}).get('value', 0),
                        'retained_earnings': balance_sheet.get('equity_attributable_to_parent', {}).get('value', 0),
                    }
                    formatted_data.append(formatted_item)
            
            self.logger.info(f"Successfully fetched {len(formatted_data)} balance sheet records for {ticker}")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error fetching balance sheet for {ticker}: {str(e)}")
            return []
    
    def get_cash_flow(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> List[Dict]:
        """
        Fetch cash flow statement data from Polygon.
        
        Args:
            ticker: Stock ticker symbol
            period: 'quarterly' or 'annual'
            limit: Number of periods to fetch
            
        Returns:
            List of cash flow data dictionaries
        """
        try:
            timeframe = 'quarterly' if period.lower() == 'quarterly' else 'annual'
            
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': timeframe,
                'limit': limit,
                'filing_date.gte': '2020-01-01'
            }
            
            self.logger.info(f"Fetching {period} cash flow for {ticker}")
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                self.logger.warning(f"No cash flow data found for {ticker}")
                return []
            
            formatted_data = []
            for result in data.get('results', []):
                if 'financials' in result and 'cash_flow_statement' in result['financials']:
                    cash_flow = result['financials']['cash_flow_statement']
                    
                    formatted_item = {
                        'ticker': ticker.upper(),
                        'period_end_date': result.get('end_date', ''),
                        'filing_date': result.get('filing_date', ''),
                        'timeframe': result.get('timeframe', ''),
                        'operating_cash_flow': cash_flow.get('net_cash_flow_from_operating_activities', {}).get('value', 0),
                        'investing_cash_flow': cash_flow.get('net_cash_flow_from_investing_activities', {}).get('value', 0),
                        'financing_cash_flow': cash_flow.get('net_cash_flow_from_financing_activities', {}).get('value', 0),
                        'free_cash_flow': cash_flow.get('net_cash_flow', {}).get('value', 0),
                    }
                    formatted_data.append(formatted_item)
            
            self.logger.info(f"Successfully fetched {len(formatted_data)} cash flow records for {ticker}")
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error fetching cash flow for {ticker}: {str(e)}")
            return []


class ProviderSelector:
    """Provider selector simplified to use only Polygon."""
    
    def __init__(self, api_keys: dict):
        """Initialize with API keys dictionary."""
        self.api_key = api_keys.get('polygon', '')
        if not self.api_key:
            raise ValueError("Polygon API key is required")
            
        self.adapter = PolygonAdapter(self.api_key)
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch income statement via Polygon only."""
        self.logger.info(f"Fetching income statement for {ticker} via Polygon")
        return self.adapter.get_income_statement(ticker, period, limit)
    
    def get_balance_sheet(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch balance sheet via Polygon only."""
        self.logger.info(f"Fetching balance sheet for {ticker} via Polygon")
        return self.adapter.get_balance_sheet(ticker, period, limit)
    
    def get_cash_flow(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch cash flow via Polygon only."""
        self.logger.info(f"Fetching cash flow for {ticker} via Polygon")
        return self.adapter.get_cash_flow(ticker, period, limit)
