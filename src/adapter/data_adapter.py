"""
Corrected data adapter module with proper field mapping for institutional template.
"""
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class PolygonAdapter:
    """Enhanced Polygon.io API adapter with correct field mapping for institutional template."""
    
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
    
    def _safe_get_value(self, data_dict: Dict, key: str, default=0) -> float:
        """Safely extract value from nested dictionary structure."""
        try:
            if key in data_dict and isinstance(data_dict[key], dict):
                return float(data_dict[key].get('value', default))
            return float(default)
        except (ValueError, TypeError):
            return float(default)
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> Dict:
        """
        Fetch comprehensive income statement data from Polygon in the format expected by institutional template.
        
        Args:
            ticker: Stock ticker symbol
            period: 'quarterly' or 'annual'
            limit: Number of periods to fetch
            
        Returns:
            Dictionary in the format expected by institutional template
        """
        try:
            # Map period parameter to Polygon's expected values
            timeframe = 'quarterly' if period.lower() == 'quarterly' else 'annual'
            
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': timeframe,
                'limit': limit
            }
            
            self.logger.info(f"Fetching {period} income statement for {ticker}")
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                self.logger.warning(f"No income statement data found for {ticker}")
                return {
                    'ticker': ticker.upper(),
                    'company_name': ticker.upper(),
                    'periods': {}
                }
            
            # Initialize the result structure expected by the template
            result = {
                'ticker': ticker.upper(),
                'company_name': ticker.upper(),  # You can enhance this with company name lookup
                'periods': {}
            }
            
            # Process each period from the API response
            for api_result in data.get('results', []):
                if 'financials' in api_result and 'income_statement' in api_result['financials']:
                    income_stmt = api_result['financials']['income_statement']
                    period_date = api_result.get('end_date', '')
                    
                    if not period_date:
                        continue
                    
                    # Log available fields for debugging (first result only)
                    if period_date == data['results'][0].get('end_date'):
                        self.logger.info(f"Available Polygon fields: {list(income_stmt.keys())}")
                    
                    # Map Polygon API fields to institutional template keys
                    # This mapping is critical - it connects what Polygon returns to what your template expects
                    period_items = {
                        # Revenue and Cost
                        'Revenues': {'value': self._safe_get_value(income_stmt, 'revenues')},
                        'CostOfGoodsSold': {'value': self._safe_get_value(income_stmt, 'cost_of_revenue')},
                        'GrossProfit': {'value': self._safe_get_value(income_stmt, 'gross_profit')},
                        
                        # Operating Expenses - try different field combinations
                        'SalesAndMarketingExpense': {'value': self._safe_get_value(income_stmt, 'selling_general_and_administrative_expenses')},
                        'ResearchAndDevelopmentExpense': {'value': self._safe_get_value(income_stmt, 'research_and_development')},
                        'GeneralAndAdministrativeExpense': {'value': self._safe_get_value(income_stmt, 'general_and_administrative_expenses')},
                        'StockBasedCompensation': {'value': self._safe_get_value(income_stmt, 'benefits_costs_expenses')},
                        'OperatingExpenses': {'value': self._safe_get_value(income_stmt, 'operating_expenses')},
                        
                        # Operating Income
                        'OperatingIncomeLoss': {'value': self._safe_get_value(income_stmt, 'operating_income_loss')},
                        
                        # Interest and Other Income/Expenses
                        'InterestExpense': {'value': self._safe_get_value(income_stmt, 'interest_expense')},
                        'InterestIncome': {'value': self._safe_get_value(income_stmt, 'interest_income')},
                        'OtherExpenses': {'value': self._safe_get_value(income_stmt, 'nonoperating_income_loss')},
                        'OtherIncome': {'value': self._safe_get_value(income_stmt, 'other_comprehensive_income_loss')},
                        
                        # Depreciation & Amortization
                        'DepreciationAndAmortization': {'value': self._safe_get_value(income_stmt, 'depreciation_and_amortization')},
                        
                        # Pre-tax and Tax
                        'IncomeLossBeforeIncomeTaxes': {'value': self._safe_get_value(income_stmt, 'income_loss_from_continuing_operations_before_tax')},
                        'IncomeTaxExpenseBenefit': {'value': self._safe_get_value(income_stmt, 'income_tax_expense_benefit')},
                        
                        # Net Income
                        'NetIncomeLoss': {'value': self._safe_get_value(income_stmt, 'net_income_loss')},
                        
                        # Share counts
                        'WeightedAverageSharesOutstandingDiluted': {'value': self._safe_get_value(income_stmt, 'weighted_average_shares_outstanding_diluted')},
                    }
                    
                    # Add the period data to the result
                    result['periods'][period_date] = {
                        'items': period_items
                    }
                    
                    # Log what was extracted for debugging
                    revenue = period_items['Revenues']['value']
                    net_income = period_items['NetIncomeLoss']['value']
                    self.logger.info(f"Extracted for {period_date}: Revenue=${revenue:,.0f}, Net Income=${net_income:,.0f}")
            
            self.logger.info(f"Successfully processed {len(result['periods'])} periods for {ticker}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching income statement for {ticker}: {str(e)}")
            return {
                'ticker': ticker.upper(),
                'company_name': ticker.upper(),
                'periods': {}
            }
    
    def debug_available_fields(self, ticker: str, period: str = 'quarterly', limit: int = 1) -> Dict:
        """
        Debug method to see all available fields in Polygon response.
        This helps identify correct field names for mapping.
        """
        try:
            timeframe = 'quarterly' if period.lower() == 'quarterly' else 'annual'
            
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': timeframe,
                'limit': limit
            }
            
            self.logger.info(f"Debugging available fields for {ticker}")
            data = self._make_request(endpoint, params)
            
            if data and 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                if 'financials' in result:
                    return {
                        'income_statement_fields': list(result['financials'].get('income_statement', {}).keys()),
                        'balance_sheet_fields': list(result['financials'].get('balance_sheet', {}).keys()),
                        'cash_flow_fields': list(result['financials'].get('cash_flow_statement', {}).keys()),
                        'sample_income_statement': result['financials'].get('income_statement', {}),
                        'end_date': result.get('end_date', 'Unknown')
                    }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error debugging fields for {ticker}: {str(e)}")
            return {}
    
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
                'limit': limit
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
                        'total_assets': self._safe_get_value(balance_sheet, 'assets'),
                        'current_assets': self._safe_get_value(balance_sheet, 'current_assets'),
                        'total_liabilities': self._safe_get_value(balance_sheet, 'liabilities'),
                        'current_liabilities': self._safe_get_value(balance_sheet, 'current_liabilities'),
                        'total_equity': self._safe_get_value(balance_sheet, 'equity'),
                        'retained_earnings': self._safe_get_value(balance_sheet, 'equity_attributable_to_parent'),
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
                'limit': limit
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
                        'operating_cash_flow': self._safe_get_value(cash_flow, 'net_cash_flow_from_operating_activities'),
                        'investing_cash_flow': self._safe_get_value(cash_flow, 'net_cash_flow_from_investing_activities'),
                        'financing_cash_flow': self._safe_get_value(cash_flow, 'net_cash_flow_from_financing_activities'),
                        'free_cash_flow': self._safe_get_value(cash_flow, 'net_cash_flow'),
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
    
    def debug_fields(self, ticker: str, period: str = 'quarterly'):
        """Debug available fields for a ticker."""
        self.logger.info(f"Debugging available fields for {ticker}")
        return self.adapter.debug_available_fields(ticker, period)
