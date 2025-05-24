"""
Data adapter module for integrating multiple financial data sources.

This module provides adapters for different financial data sources,
allowing the parser to work with SEC EDGAR, third-party APIs, or local files.
"""
import os
import logging
import json
import requests
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from ..config import Config


class DataAdapter(ABC):
    """Abstract base class for data adapters."""
    
    @abstractmethod
    def get_income_statement(self, 
                           ticker: str, 
                           period: str = 'quarterly',
                           limit: int = 20) -> Dict:
        """Get income statement data for a company.
        
        Args:
            ticker: Ticker symbol of the company.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to return.
            
        Returns:
            Income statement data.
        """
        pass


class PolygonAdapter(DataAdapter):
    """Adapter for Polygon.io API."""
    
    def __init__(self, api_key: str):
        """Initialize Polygon adapter.
        
        Args:
            api_key: Polygon API key.
        """
        self.api_key = api_key
        self.base_url = "https://api.polygon.io"
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, 
                           ticker: str, 
                           period: str = 'quarterly',
                           limit: int = 20) -> Dict:
        """Get income statement data from Polygon.
        
        Args:
            ticker: Ticker symbol of the company.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to return.
            
        Returns:
            Income statement data.
        """
        timeframe = 'Q' if period == 'quarterly' else 'A'
        
        try:
            url = f"{self.base_url}/vX/reference/financials?ticker={ticker}&timeframe={timeframe}&limit={limit}&apiKey={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Transform to standardized format
            return self._transform_polygon_data(data)
            
        except Exception as e:
            self.logger.error(f"Error fetching income statement from Polygon for {ticker}: {str(e)}")
            return {}
    
    def _transform_polygon_data(self, data: Dict) -> Dict:
        """Transform Polygon data to standardized format.
        
        Args:
            data: Raw Polygon data.
            
        Returns:
            Standardized income statement data.
        """
        result = {
            'ticker': '',
            'company_name': '',
            'periods': {}
        }
        
        if 'results' not in data or not data['results']:
            return result
        
        # Extract company info
        result['ticker'] = data['results'][0].get('ticker', '')
        
        # Process each period
        for period_data in data['results']:
            # Get period end date
            period_end = period_data.get('end_date', '')
            if not period_end:
                continue
            
            # Extract income statement items
            income_statement = period_data.get('financials', {}).get('income_statement', {})
            
            period_result = {
                'period_end_date': period_end,
                'period_type': 'quarterly' if period_data.get('timeframe') == 'Q' else 'annual',
                'currency': period_data.get('currency', 'USD'),
                'items': {}
            }
            
            # Map Polygon fields to standardized fields
            field_mapping = {
                'revenues': 'Revenues',
                'cost_of_revenue': 'CostOfRevenue',
                'gross_profit': 'GrossProfit',
                'operating_expenses': 'OperatingExpenses',
                'operating_income': 'OperatingIncomeLoss',
                'net_income_loss': 'NetIncomeLoss',
                'basic_earnings_per_share': 'EarningsPerShareBasic',
                'diluted_earnings_per_share': 'EarningsPerShareDiluted'
            }
            
            for polygon_field, std_field in field_mapping.items():
                if polygon_field in income_statement:
                    period_result['items'][std_field] = {
                        'value': income_statement[polygon_field].get('value', 0),
                        'unit': income_statement[polygon_field].get('unit', '')
                    }
            
            # Add to periods dictionary
            result['periods'][period_end] = period_result
        
        return result


class SimFinAdapter(DataAdapter):
    """Adapter for SimFin API."""
    
    def __init__(self, api_key: str):
        """Initialize SimFin adapter.
        
        Args:
            api_key: SimFin API key.
        """
        self.api_key = api_key
        self.base_url = "https://simfin.com/api/v2"
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, 
                           ticker: str, 
                           period: str = 'quarterly',
                           limit: int = 20) -> Dict:
        """Get income statement data from SimFin.
        
        Args:
            ticker: Ticker symbol of the company.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to return.
            
        Returns:
            Income statement data.
        """
        statement_type = 'pl' # profit and loss (income statement)
        period_type = 'Q' if period == 'quarterly' else 'FY'
        
        try:
            # First get company ID
            company_url = f"{self.base_url}/companies/ticker/{ticker}?api-key={self.api_key}"
            response = requests.get(company_url)
            response.raise_for_status()
            company_data = response.json()
            
            if not company_data or 'id' not in company_data[0]:
                self.logger.error(f"Could not find company ID for ticker {ticker}")
                return {}
            
            company_id = company_data[0]['id']
            company_name = company_data[0].get('name', '')
            
            # Get income statement data
            url = f"{self.base_url}/companies/id/{company_id}/statements/{statement_type}/{period_type}?api-key={self.api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Transform to standardized format
            return self._transform_simfin_data(data, ticker, company_name)
            
        except Exception as e:
            self.logger.error(f"Error fetching income statement from SimFin for {ticker}: {str(e)}")
            return {}
    
    def _transform_simfin_data(self, data: Dict, ticker: str, company_name: str) -> Dict:
        """Transform SimFin data to standardized format.
        
        Args:
            data: Raw SimFin data.
            ticker: Ticker symbol.
            company_name: Company name.
            
        Returns:
            Standardized income statement data.
        """
        result = {
            'ticker': ticker,
            'company_name': company_name,
            'periods': {}
        }
        
        if not data or 'columns' not in data or 'data' not in data:
            return result
        
        # Get column indices
        columns = data['columns']
        try:
            date_index = columns.index('fiscalPeriod')
            
            # Map SimFin fields to standardized fields
            field_mapping = {
                'Revenue': 'Revenues',
                'Cost of Revenue': 'CostOfRevenue',
                'Gross Profit': 'GrossProfit',
                'Operating Expenses': 'OperatingExpenses',
                'Operating Income (Loss)': 'OperatingIncomeLoss',
                'Net Income': 'NetIncomeLoss',
                'EPS (Basic)': 'EarningsPerShareBasic',
                'EPS (Diluted)': 'EarningsPerShareDiluted'
            }
            
            field_indices = {}
            for simfin_field, std_field in field_mapping.items():
                if simfin_field in columns:
                    field_indices[std_field] = columns.index(simfin_field)
            
            # Process each row (period)
            for row in data['data']:
                period_end = row[date_index]
                
                period_result = {
                    'period_end_date': period_end,
                    'period_type': 'quarterly' if 'Q' in period_end else 'annual',
                    'currency': 'USD',  # SimFin typically uses USD
                    'items': {}
                }
                
                # Extract values for each field
                for std_field, index in field_indices.items():
                    if 0 <= index < len(row) and row[index] is not None:
                        period_result['items'][std_field] = {
                            'value': row[index],
                            'unit': 'USD'
                        }
                
                # Add to periods dictionary
                result['periods'][period_end] = period_result
                
                # Limit to requested number of periods
                if len(result['periods']) >= 20:
                    break
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error transforming SimFin data: {str(e)}")
            return result


class AlphaVantageAdapter(DataAdapter):
    """Adapter for Alpha Vantage API."""
    
    def __init__(self, api_key: str):
        """Initialize Alpha Vantage adapter.
        
        Args:
            api_key: Alpha Vantage API key.
        """
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, 
                           ticker: str, 
                           period: str = 'quarterly',
                           limit: int = 20) -> Dict:
        """Get income statement data from Alpha Vantage.
        
        Args:
            ticker: Ticker symbol of the company.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to return.
            
        Returns:
            Income statement data.
        """
        function = 'INCOME_STATEMENT'
        
        try:
            params = {
                'function': function,
                'symbol': ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Transform to standardized format
            return self._transform_alphavantage_data(data, ticker, period, limit)
            
        except Exception as e:
            self.logger.error(f"Error fetching income statement from Alpha Vantage for {ticker}: {str(e)}")
            return {}
    
    def _transform_alphavantage_data(self, data: Dict, ticker: str, period: str, limit: int) -> Dict:
        """Transform Alpha Vantage data to standardized format.
        
        Args:
            data: Raw Alpha Vantage data.
            ticker: Ticker symbol.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to return.
            
        Returns:
            Standardized income statement data.
        """
        result = {
            'ticker': ticker,
            'company_name': data.get('Symbol', ticker),
            'periods': {}
        }
        
        # Determine which data to use based on period
        if period == 'quarterly':
            periods_data = data.get('quarterlyReports', [])
        else:
            periods_data = data.get('annualReports', [])
        
        # Limit the number of periods
        periods_data = periods_data[:limit]
        
        # Map Alpha Vantage fields to standardized fields
        field_mapping = {
            'totalRevenue': 'Revenues',
            'costOfRevenue': 'CostOfRevenue',
            'grossProfit': 'GrossProfit',
            'operatingExpenses': 'OperatingExpenses',
            'operatingIncome': 'OperatingIncomeLoss',
            'netIncome': 'NetIncomeLoss',
            'ebitda': 'EBITDA',
            'eps': 'EarningsPerShareBasic'
        }
        
        # Process each period
        for period_data in periods_data:
            period_end = period_data.get('fiscalDateEnding', '')
            if not period_end:
                continue
            
            period_result = {
                'period_end_date': period_end,
                'period_type': 'quarterly' if period == 'quarterly' else 'annual',
                'currency': 'USD',  # Alpha Vantage typically uses USD
                'items': {}
            }
            
            # Extract values for each field
            for av_field, std_field in field_mapping.items():
                if av_field in period_data and period_data[av_field] != 'None':
                    try:
                        value = float(period_data[av_field])
                        period_result['items'][std_field] = {
                            'value': value,
                            'unit': 'USD'
                        }
                    except (ValueError, TypeError):
                        pass  # Skip if value can't be converted to float
            
            # Add to periods dictionary
            result['periods'][period_end] = period_result
        
        return result


class FinnhubAdapter(DataAdapter):
    """Adapter for Finnhub API."""
    
    def __init__(self, api_key: str):
        """Initialize Finnhub adapter.
        
        Args:
            api_key: Finnhub API key.
        """
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, 
                           ticker: str, 
                           period: str = 'quarterly',
                           limit: int = 20) -> Dict:
        """Get income statement data from Finnhub.
        
        Args:
            ticker: Ticker symbol of the company.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to return.
            
        Returns:
            Income statement data.
        """
        freq = 'quarterly' if period == 'quarterly' else 'annual'
        
        try:
            headers = {
                'X-Finnhub-Token': self.api_key
            }
            
            url = f"{self.base_url}/stock/financials?symbol={ticker}&statement=ic&freq={freq}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Transform to standardized format
            return self._transform_finnhub_data(data, ticker, period, limit)
            
        except Exception as e:
            self.logger.error(f"Error fetching income statement from Finnhub for {ticker}: {str(e)}")
            return {}
    
    def _transform_finnhub_data(self, data: Dict, ticker: str, period: str, limit: int) -> Dict:
        """Transform Finnhub data to standardized format.
        
        Args:
            data: Raw Finnhub data.
            ticker: Ticker symbol.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to return.
            
        Returns:
            Standardized income statement data.
        """
        result = {
            'ticker': ticker,
            'company_name': data.get('symbol', ticker),
            'periods': {}
        }
        
        if 'financials' not in data or not data['financials']:
            return result
        
        # Limit the number of periods
        financials = data['financials'][:limit]
        
        # Map Finnhub fields to standardized fields
        field_mapping = {
            'revenue': 'Revenues',
            'cogs': 'CostOfRevenue',
            'grossProfit': 'GrossProfit',
            'totalOpex': 'OperatingExpenses',
            'ebit': 'OperatingIncomeLoss',
            'netIncome': 'NetIncomeLoss',
            'ebitda': 'EBITDA',
            'eps': 'EarningsPerShareBasic'
        }
        
        # Process each period
        for financial in financials:
            period_end = financial.get('period', '')
            if not period_end:
                continue
            
            period_result = {
                'period_end_date': period_end,
                'period_type': period,
                'currency': 'USD',  # Finnhub typically uses USD
                'items': {}
            }
            
            # Extract values for each field
            for fh_field, std_field in field_mapping.items():
                if fh_field in financial and financial[fh_field] is not None:
                    period_result['items'][std_field] = {
                        'value': financial[fh_field],
                        'unit': 'USD'
                    }
            
            # Add to periods dictionary
            result['periods'][period_end] = period_result
        
        return result


class LocalFileAdapter(DataAdapter):
    """Adapter for local file data."""
    
    def __init__(self, data_dir: str):
        """Initialize local file adapter.
        
        Args:
            data_dir: Directory containing local data files.
        """
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
    
    def get_income_statement(self, 
                           ticker: str, 
                           period: str = 'quarterly',
                           limit: int = 20) -> Dict:
        """Get income statement data from local files.
        
        Args:
            ticker: Ticker symbol of the company.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to return.
            
        Returns:
            Income statement data.
        """
        # Look for a JSON file with income statement data
        file_path = os.path.join(self.data_dir, f"{ticker}_income_statement.json")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Filter by period type if needed
                if period in ['quarterly', 'annual']:
                    filtered_periods = {}
                    for period_key, period_data in data.get('periods', {}).items():
                        if period_data.get('period_type') == period:
                            filtered_periods[period_key] = period_data
                    
                    # Replace with filtered periods
                    data['periods'] = filtered_periods
                
                # Limit the number of periods
                if limit > 0 and len(data.get('periods', {})) > limit:
                    # Sort periods by date (descending)
                    sorted_periods = sorted(data.get('periods', {}).items(), 
                                           key=lambda x: x[1].get('period_end_date', ''),
                                           reverse=True)
                    
                    # Take only the most recent periods
                    limited_periods = dict(sorted_periods[:limit])
                    data['periods'] = limited_periods
                
                return data
                
            except Exception as e:
                self.logger.error(f"Error reading local income statement data for {ticker}: {str(e)}")
                return {}
        else:
            self.logger.warning(f"No local income statement data found for {ticker} at {file_path}")
            return {}
    
    def save_income_statement(self, ticker: str, data: Dict) -> bool:
        """Save income statement data to a local file.
        
        Args:
            ticker: Ticker symbol of the company.
            data: Income statement data to save.
            
        Returns:
            True if successful, False otherwise.
        """
        file_path = os.path.join(self.data_dir, f"{ticker}_income_statement.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved income statement data for {ticker} to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving income statement data for {ticker}: {str(e)}")
            return False


class AdapterFactory:
    """Factory for creating data adapters."""
    
    @staticmethod
    def create_adapter(adapter_type: str, config: Dict) -> DataAdapter:
        """Create a data adapter.
        
        Args:
            adapter_type: Type of adapter to create.
            config: Configuration for the adapter.
            
        Returns:
            Data adapter instance.
            
        Raises:
            ValueError: If the adapter type is not supported.
        """
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
