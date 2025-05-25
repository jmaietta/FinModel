"""
Final production adapter with clean SG&A mapping using other_operating_expenses.
Professional approach - shows what's available vs. what's missing.
"""
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class PolygonAdapter:
    """Final production Polygon adapter with realistic field mapping."""
    
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
    
    def _safe_get_value(self, data_dict: Dict, key: str, default=None) -> Optional[float]:
        """Safely extract value from nested dictionary structure."""
        try:
            if key in data_dict and isinstance(data_dict[key], dict):
                value = data_dict[key].get('value')
                return float(value) if value is not None else None
            return default
        except (ValueError, TypeError):
            return default
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> Dict:
        """
        Get income statement with realistic field mapping based on Polygon's actual data structure.
        """
        try:
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
            
            # Initialize the result
            result = {
                'ticker': ticker.upper(),
                'company_name': ticker.upper(),
                'periods': {},
                'data_source_notes': {
                    'provider': 'Polygon.io',
                    'data_policy': 'Actual data only - no estimates',
                    'field_limitations': {
                        'sales_marketing_separate': 'Not available - combined in other_operating_expenses',
                        'general_admin_separate': 'Not available - combined in other_operating_expenses', 
                        'stock_compensation': 'Not separately disclosed',
                        'interest_income_expense': 'Not separately disclosed',
                        'depreciation_amortization': 'Not separately disclosed'
                    }
                }
            }
            
            # Process each period
            for api_result in data.get('results', []):
                if 'financials' in api_result and 'income_statement' in api_result['financials']:
                    income_stmt = api_result['financials']['income_statement']
                    period_date = api_result.get('end_date', '')
                    
                    if not period_date:
                        continue
                    
                    # Create period items with realistic mapping
                    period_items = {
                        # AVAILABLE FIELDS (high confidence - directly from Polygon)
                        'Revenues': {
                            'value': self._safe_get_value(income_stmt, 'revenues'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        'CostOfGoodsSold': {
                            'value': self._safe_get_value(income_stmt, 'cost_of_revenue'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        'GrossProfit': {
                            'value': self._safe_get_value(income_stmt, 'gross_profit'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        'ResearchAndDevelopmentExpense': {
                            'value': self._safe_get_value(income_stmt, 'research_and_development'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        'OperatingExpenses': {
                            'value': self._safe_get_value(income_stmt, 'operating_expenses'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        'OperatingIncomeLoss': {
                            'value': self._safe_get_value(income_stmt, 'operating_income_loss'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        'IncomeLossBeforeIncomeTaxes': {
                            'value': self._safe_get_value(income_stmt, 'income_loss_from_continuing_operations_before_tax'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        'IncomeTaxExpenseBenefit': {
                            'value': self._safe_get_value(income_stmt, 'income_tax_expense_benefit'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        'NetIncomeLoss': {
                            'value': self._safe_get_value(income_stmt, 'net_income_loss'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        'WeightedAverageSharesOutstandingDiluted': {
                            'value': self._safe_get_value(income_stmt, 'diluted_average_shares'),
                            'source': 'polygon_direct',
                            'confidence': 'high'
                        },
                        
                        # COMBINED SG&A (available as other_operating_expenses)
                        'SellingGeneralAndAdministrativeExpenses': {
                            'value': self._safe_get_value(income_stmt, 'other_operating_expenses'),
                            'source': 'polygon_other_operating_expenses',
                            'confidence': 'high',
                            'note': 'Combined Sales & Marketing + General & Administrative expenses'
                        },
                        
                        # UNAVAILABLE FIELDS (not separately disclosed by Polygon)
                        'SalesAndMarketingExpense': {
                            'value': None,
                            'source': 'unavailable',
                            'confidence': 'none',
                            'note': 'Not separately disclosed - included in SG&A combined figure'
                        },
                        'GeneralAndAdministrativeExpense': {
                            'value': None,
                            'source': 'unavailable',
                            'confidence': 'none',
                            'note': 'Not separately disclosed - included in SG&A combined figure'
                        },
                        'StockBasedCompensation': {
                            'value': None,
                            'source': 'unavailable',
                            'confidence': 'none',
                            'note': 'Not separately disclosed by Polygon - likely included in SG&A'
                        },
                        'InterestExpense': {
                            'value': None,
                            'source': 'unavailable',
                            'confidence': 'none',
                            'note': 'Not separately disclosed by Polygon'
                        },
                        'InterestIncome': {
                            'value': None,
                            'source': 'unavailable',
                            'confidence': 'none',
                            'note': 'Not separately disclosed by Polygon'
                        },
                        'OtherExpenses': {
                            'value': self._safe_get_value(income_stmt, 'nonoperating_income_loss'),
                            'source': 'polygon_nonoperating',
                            'confidence': 'medium',
                            'note': 'Mapped to nonoperating_income_loss'
                        },
                        'OtherIncome': {
                            'value': None,
                            'source': 'unavailable',
                            'confidence': 'none',
                            'note': 'Not separately disclosed by Polygon'
                        },
                        'DepreciationAndAmortization': {
                            'value': None,
                            'source': 'unavailable',
                            'confidence': 'none',
                            'note': 'Not separately disclosed by Polygon'
                        }
                    }
                    
                    # Add this period to the result
                    result['periods'][period_date] = {
                        'items': period_items
                    }
                    
                    # Log summary for transparency
                    revenue = period_items['Revenues']['value'] or 0
                    sga = period_items['SellingGeneralAndAdministrativeExpenses']['value'] or 0
                    rd = period_items['ResearchAndDevelopmentExpense']['value'] or 0
                    net_income = period_items['NetIncomeLoss']['value'] or 0
                    
                    self.logger.info(f"PROCESSED {period_date}:")
                    self.logger.info(f"  ✅ Revenue: ${revenue/1000000:.0f}M (actual)")
                    self.logger.info(f"  ✅ R&D: ${rd/1000000:.0f}M (actual)")
                    self.logger.info(f"  ✅ SG&A Combined: ${sga/1000000:.0f}M (actual)")
                    self.logger.info(f"  ❌ Sales & Marketing: N/A (not separately available)")
                    self.logger.info(f"  ❌ G&A: N/A (not separately available)")
                    self.logger.info(f"  ✅ Net Income: ${net_income/1000000:.0f}M (actual)")
            
            periods_count = len(result['periods'])
            self.logger.info(f"Successfully processed {periods_count} periods for {ticker}")
            
            # Log data quality summary
            self.logger.info("DATA QUALITY SUMMARY:")
            self.logger.info("  ✅ High quality: Revenue, R&D, SG&A (combined), Operating Income, Net Income")
            self.logger.info("  ❌ Not available: Sales & Marketing (separate), G&A (separate), Stock Comp, Interest, D&A")
            self.logger.info("  📊 Professional approach: Show actual data availability, no false estimates")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching income statement for {ticker}: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'ticker': ticker.upper(),
                'company_name': ticker.upper(),
                'periods': {}
            }
    
    def get_balance_sheet(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> List[Dict]:
        """Fetch balance sheet data from Polygon."""
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
        """Fetch cash flow statement data from Polygon."""
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
    """Provider selector with realistic data expectations."""
    
    def __init__(self, api_keys: dict):
        """Initialize with API keys dictionary."""
        self.api_key = api_keys.get('polygon', '')
        if not self.api_key:
            raise ValueError("Polygon API key is required")
            
        self.adapter = PolygonAdapter(self.api_key)
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch income statement with realistic field expectations."""
        self.logger.info(f"Fetching income statement for {ticker} - professional data quality approach")
        return self.adapter.get_income_statement(ticker, period, limit)
    
    def get_balance_sheet(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch balance sheet via Polygon only."""
        self.logger.info(f"Fetching balance sheet for {ticker} via Polygon")
        return self.adapter.get_balance_sheet(ticker, period, limit)
    
    def get_cash_flow(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch cash flow via Polygon only."""
        self.logger.info(f"Fetching cash flow for {ticker} via Polygon")
        return self.adapter.get_cash_flow(ticker, period, limit)
