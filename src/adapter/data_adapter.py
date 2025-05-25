"""
Enhanced Excel generation module with better debugging and data transformation.
"""
import os
import logging
from typing import Dict, Optional

# Import from sec_parser
import sys
sys.path.append('/home/ubuntu/sec_parser')
from src.formatter.institutional_template import InstitutionalDetailedTemplate
from src.provider_selection import ProviderSelector

class ExcelGenerator:
    """Enhanced Excel report generator with debugging and data transformation."""
    
    def __init__(self, api_keys: Dict[str, str], output_dir: str = None):
        """Initialize the Excel generator."""
        self.logger = logging.getLogger(__name__)
        
        # Set output directory
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
        else:
            self.output_dir = output_dir
            
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize provider selector
        self.provider_selector = ProviderSelector(api_keys)
        
        # Initialize Excel template
        self.template = InstitutionalDetailedTemplate()
    
    def _transform_list_to_periods_format(self, data_list: list, ticker: str) -> Dict:
        """
        Transform list format data to periods format expected by institutional template.
        
        Args:
            data_list: List of period dictionaries from data adapter
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary in institutional template format
        """
        result = {
            'ticker': ticker.upper(),
            'company_name': ticker.upper(),
            'periods': {}
        }
        
        if not data_list:
            self.logger.warning(f"No data to transform for {ticker}")
            return result
        
        self.logger.info(f"Transforming {len(data_list)} periods for {ticker}")
        
        # Define the institutional field mapping
        field_mapping = {
            # Map from data adapter fields to institutional template fields
            'revenue': 'Revenues',
            'Revenues': 'Revenues',
            'cost_of_revenue': 'CostOfGoodsSold',
            'CostOfGoodsSold': 'CostOfGoodsSold',
            'gross_profit': 'GrossProfit',
            'GrossProfit': 'GrossProfit',
            'operating_expenses': 'OperatingExpenses',
            'OperatingExpenses': 'OperatingExpenses',
            'operating_income': 'OperatingIncomeLoss',
            'OperatingIncomeLoss': 'OperatingIncomeLoss',
            'net_income': 'NetIncomeLoss',
            'NetIncomeLoss': 'NetIncomeLoss',
            'basic_eps': 'BasicEarningsPerShare',
            'diluted_eps': 'DilutedEarningsPerShare',
            'WeightedAverageSharesOutstandingDiluted': 'WeightedAverageSharesOutstandingDiluted',
            # Add more mappings as needed
            'SalesAndMarketingExpense': 'SalesAndMarketingExpense',
            'ResearchAndDevelopmentExpense': 'ResearchAndDevelopmentExpense',
            'GeneralAndAdministrativeExpense': 'GeneralAndAdministrativeExpense',
            'StockBasedCompensation': 'StockBasedCompensation',
            'InterestExpense': 'InterestExpense',
            'InterestIncome': 'InterestIncome',
            'OtherExpenses': 'OtherExpenses',
            'OtherIncome': 'OtherIncome',
            'DepreciationAndAmortization': 'DepreciationAndAmortization',
            'IncomeLossBeforeIncomeTaxes': 'IncomeLossBeforeIncomeTaxes',
            'IncomeTaxExpenseBenefit': 'IncomeTaxExpenseBenefit',
        }
        
        for period_data in data_list:
            period_date = period_data.get('period_end_date', '')
            if not period_date:
                self.logger.warning(f"Period missing end_date: {period_data}")
                continue
            
            # Transform the data for this period
            period_items = {}
            
            # Log available fields in this period
            available_fields = [k for k in period_data.keys() if k not in ['ticker', 'period_end_date', 'filing_date', 'timeframe']]
            self.logger.info(f"Period {period_date} available fields: {available_fields}")
            
            # Map each field from the data to institutional format
            for source_field, target_field in field_mapping.items():
                if source_field in period_data:
                    value = period_data[source_field]
                    period_items[target_field] = {'value': value}
                    
                    # Log non-zero values
                    if value != 0:
                        self.logger.info(f"  {source_field} -> {target_field}: {value:,.0f}")
            
            # Add this period to result
            result['periods'][period_date] = {
                'items': period_items
            }
        
        self.logger.info(f"Transformed data: {len(result['periods'])} periods with financial data")
        return result
    
    def generate_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> Optional[str]:
        """Generate Excel income statement for the specified ticker."""
        try:
            # Normalize ticker
            ticker = ticker.strip().upper()
            
            self.logger.info(f"Generating income statement for {ticker}")
            
            # Get income statement data using provider selector
            raw_data = self.provider_selector.get_income_statement(ticker, period, limit)
            
            # Enhanced debugging: Log what we actually received
            self.logger.info(f"Raw data type: {type(raw_data)}")
            
            if isinstance(raw_data, list):
                self.logger.info(f"Received list with {len(raw_data)} items")
                if raw_data:
                    sample_item = raw_data[0]
                    self.logger.info(f"Sample item keys: {list(sample_item.keys())}")
                    self.logger.info(f"Sample period_end_date: {sample_item.get('period_end_date', 'Missing')}")
                
                # Transform list format to periods format
                income_statement = self._transform_list_to_periods_format(raw_data, ticker)
                
            elif isinstance(raw_data, dict):
                self.logger.info(f"Received dict with keys: {list(raw_data.keys())}")
                if 'periods' in raw_data:
                    self.logger.info(f"Dict has {len(raw_data['periods'])} periods")
                    income_statement = raw_data
                else:
                    self.logger.error(f"Dict missing 'periods' key")
                    return None
            else:
                self.logger.error(f"Unexpected data type: {type(raw_data)}")
                return None
            
            # Check if we have valid transformed data
            if not income_statement or 'periods' not in income_statement or not income_statement['periods']:
                self.logger.error(f"No valid income statement data for {ticker}")
                self.logger.error(f"Final income_statement: {income_statement}")
                return None
            
            # Log final structure
            periods_count = len(income_statement['periods'])
            self.logger.info(f"Final data structure: {periods_count} periods ready for Excel generation")
            
            if periods_count > 0:
                sample_period_key = list(income_statement['periods'].keys())[0]
                sample_period = income_statement['periods'][sample_period_key]
                items_count = len(sample_period.get('items', {}))
                self.logger.info(f"Sample period {sample_period_key} has {items_count} line items")
                
                # Show sample values
                sample_items = sample_period.get('items', {})
                for item_key in ['Revenues', 'NetIncomeLoss', 'OperatingIncomeLoss']:
                    if item_key in sample_items:
                        value = sample_items[item_key].get('value', 0)
                        self.logger.info(f"  Sample {item_key}: {value:,.0f}")
            
            # Generate Excel file
            output_path = os.path.join(self.output_dir, f"{ticker}_Income_Statement.xlsx")
            
            # Create Excel file using institutional template
            self.template.create_template(income_statement, output_path)
            
            self.logger.info(f"Excel income statement generated for {ticker} at {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating income statement for {ticker}: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
