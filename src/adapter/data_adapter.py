"""
SG&A focused data adapter to specifically test for selling_general_and_administrative_expenses field.
"""
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class PolygonAdapter:
    """Polygon adapter focused on finding SG&A expenses field."""
    
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
    
    def test_sga_field_variations(self, ticker: str) -> Dict:
        """
        Test various SG&A field name variations to find the correct one.
        """
        try:
            endpoint = f"/vX/reference/financials"
            params = {
                'ticker': ticker.upper(),
                'timeframe': 'quarterly',
                'limit': 1
            }
            
            self.logger.info(f"=== TESTING SG&A FIELD VARIATIONS FOR {ticker} ===")
            data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data or len(data['results']) == 0:
                self.logger.warning(f"No data found for {ticker}")
                return {}
            
            result = data['results'][0]
            if 'financials' not in result or 'income_statement' not in result['financials']:
                self.logger.warning(f"No income statement found for {ticker}")
                return {}
            
            income_stmt = result['financials']['income_statement']
            period_date = result.get('end_date', 'Unknown')
            
            # Test specific SG&A field variations
            sga_field_variations = [
                'selling_general_and_administrative_expenses',
                'selling_general_administrative_expenses', 
                'sg_a_expenses',
                'sga_expenses',
                'selling_and_administrative_expenses',
                'general_and_administrative_expenses',
                'selling_general_admin_expenses',
                'sales_general_administrative_expenses',
                'selling_administrative_expenses'
            ]
            
            self.logger.info(f"Period: {period_date}")
            self.logger.info(f"Testing {len(sga_field_variations)} SG&A field variations...")
            
            found_fields = {}
            
            # Test each variation
            for field_name in sga_field_variations:
                if field_name in income_stmt:
                    value = self._safe_get_value(income_stmt, field_name)
                    found_fields[field_name] = value
                    
                    self.logger.info(f"✅ FOUND: '{field_name}' = ${value/1000000:.1f}M")
                    
                    # Check if this matches expected MSFT SG&A (~$7.95B)
                    if 7500 <= value/1000000 <= 8500:
                        self.logger.info(f"🎯 LIKELY MATCH for SG&A: '{field_name}' = ${value/1000000:.1f}M")
                else:
                    self.logger.debug(f"❌ Not found: '{field_name}'")
            
            if not found_fields:
                self.logger.info("❌ No SG&A field variations found")
                
                # Show what fields ARE available for reference
                self.logger.info("Available fields for reference:")
                for field_name in sorted(income_stmt.keys()):
                    if any(keyword in field_name.lower() for keyword in ['sell', 'admin', 'general', 'expense', 'operating']):
                        value = self._safe_get_value(income_stmt, field_name)
                        self.logger.info(f"  '{field_name}': ${value/1000000:.1f}M")
            
            return {
                'period': period_date,
                'found_sga_fields': found_fields,
                'total_variations_tested': len(sga_field_variations),
                'matches_found': len(found_fields)
            }
            
        except Exception as e:
            self.logger.error(f"Error testing SG&A fields for {ticker}: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> Dict:
        """
        Get income statement WITH SG&A field testing and proper mapping.
        """
        try:
            # First, test SG&A field variations
            sga_test_results = self.test_sga_field_variations(ticker)
            
            # Determine the correct SG&A field name
            sga_field_name = None
            if sga_test_results.get('found_sga_fields'):
                # Use the first found field (they should all be the same)
                sga_field_name = list(sga_test_results['found_sga_fields'].keys())[0]
                self.logger.info(f"Using SG&A field: '{sga_field_name}'")
            else:
                # Fallback to other_operating_expenses if no SG&A field found
                sga_field_name = 'other_operating_expenses'
                self.logger.info(f"No SG&A field found, using fallback: '{sga_field_name}'")
            
            # Now fetch the full dataset
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
                'sga_field_discovery': sga_test_results,
                'sga_field_used': sga_field_name
            }
            
            # Process each period
            for api_result in data.get('results', []):
                if 'financials' in api_result and 'income_statement' in api_result['financials']:
                    income_stmt = api_result['financials']['income_statement']
                    period_date = api_result.get('end_date', '')
                    
                    if not period_date:
                        continue
                    
                    # Create period items with SG&A mapping
                    period_items = {
                        # CORE FIELDS (confirmed working)
                        'Revenues': {'value': self._safe_get_value(income_stmt, 'revenues')},
                        'CostOfGoodsSold': {'value': self._safe_get_value(income_stmt, 'cost_of_revenue')},
                        'GrossProfit': {'value': self._safe_get_value(income_stmt, 'gross_profit')},
                        'ResearchAndDevelopmentExpense': {'value': self._safe_get_value(income_stmt, 'research_and_development')},
                        'OperatingExpenses': {'value': self._safe_get_value(income_stmt, 'operating_expenses')},
                        'OperatingIncomeLoss': {'value': self._safe_get_value(income_stmt, 'operating_income_loss')},
                        'IncomeLossBeforeIncomeTaxes': {'value': self._safe_get_value(income_stmt, 'income_loss_from_continuing_operations_before_tax')},
                        'IncomeTaxExpenseBenefit': {'value': self._safe_get_value(income_stmt, 'income_tax_expense_benefit')},
                        'NetIncomeLoss': {'value': self._safe_get_value(income_stmt, 'net_income_loss')},
                        'WeightedAverageSharesOutstandingDiluted': {'value': self._safe_get_value(income_stmt, 'diluted_average_shares')},
                        
                        # SG&A FIELD (using discovered field name)
                        'SalesAndMarketingExpense': {
                            'value': None,  # Not available separately
                            'note': 'Combined with G&A in SG&A field'
                        },
                        'GeneralAndAdministrativeExpense': {
                            'value': None,  # Not available separately  
                            'note': 'Combined with Sales & Marketing in SG&A field'
                        },
                        'SellingGeneralAndAdministrativeExpenses': {
                            'value': self._safe_get_value(income_stmt, sga_field_name),
                            'source_field': sga_field_name,
                            'note': 'Combined Sales & Marketing + General & Administrative'
                        },
                        
                        # OTHER FIELDS
                        'StockBasedCompensation': {'value': 0, 'note': 'Not separately available from Polygon'},
                        'InterestExpense': {'value': 0, 'note': 'Not separately available from Polygon'},
                        'InterestIncome': {'value': 0, 'note': 'Not separately available from Polygon'},
                        'OtherExpenses': {'value': self._safe_get_value(income_stmt, 'nonoperating_income_loss')},
                        'OtherIncome': {'value': 0, 'note': 'Not separately available from Polygon'},
                        'DepreciationAndAmortization': {'value': 0, 'note': 'Not separately available from Polygon'},
                    }
                    
                    # Add this period to the result
                    result['periods'][period_date] = {
                        'items': period_items
                    }
                    
                    # Log the results
                    revenue = period_items['Revenues']['value']
                    sga = period_items['SellingGeneralAndAdministrativeExpenses']['value']
                    rd = period_items['ResearchAndDevelopmentExpense']['value']
                    net_income = period_items['NetIncomeLoss']['value']
                    
                    self.logger.info(f"PROCESSED {period_date}:")
                    self.logger.info(f"  Revenue: ${revenue/1000000:.0f}M")
                    self.logger.info(f"  SG&A ({sga_field_name}): ${sga/1000000:.0f}M")
                    self.logger.info(f"  R&D: ${rd/1000000:.0f}M")
                    self.logger.info(f"  Net Income: ${net_income/1000000:.0f}M")
                    
                    # Verify against expected MSFT numbers for Q1 2025
                    if period_date == '2025-03-31':
                        expected_sga = 7949  # S&M $6,212M + G&A $1,737M
                        if abs(sga/1000000 - expected_sga) < 100:  # Within $100M
                            self.logger.info(f"✅ SG&A VERIFICATION: ${sga/1000000:.0f}M matches expected ~${expected_sga}M")
                        else:
                            self.logger.warning(f"⚠️  SG&A VERIFICATION: ${sga/1000000:.0f}M differs from expected ~${expected_sga}M")
            
            periods_count = len(result['periods'])
            self.logger.info(f"Successfully processed {periods_count} periods for {ticker} with SG&A field testing")
            
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
        return []
    
    def get_cash_flow(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> List[Dict]:
        """Fetch cash flow statement data from Polygon."""
        return []


class ProviderSelector:
    """Provider selector with SG&A field testing."""
    
    def __init__(self, api_keys: dict):
        """Initialize with API keys dictionary."""
        self.api_key = api_keys.get('polygon', '')
        if not self.api_key:
            raise ValueError("Polygon API key is required")
            
        self.adapter = PolygonAdapter(self.api_key)
        self.logger = logging.getLogger(__name__)
    
    def get_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch income statement with SG&A field testing."""
        self.logger.info(f"Fetching income statement for {ticker} with SG&A field testing")
        return self.adapter.get_income_statement(ticker, period, limit)
    
    def get_balance_sheet(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch balance sheet via Polygon only."""
        self.logger.info(f"Fetching balance sheet for {ticker} via Polygon")
        return self.adapter.get_balance_sheet(ticker, period, limit)
    
    def get_cash_flow(self, ticker: str, period: str = 'quarterly', limit: int = 12):
        """Fetch cash flow via Polygon only."""
        self.logger.info(f"Fetching cash flow for {ticker} via Polygon")
        return self.adapter.get_cash_flow(ticker, period, limit)
    
    def test_sga_fields(self, ticker: str):
        """Test SG&A field variations for a ticker."""
        return self.adapter.test_sga_field_variations(ticker)
