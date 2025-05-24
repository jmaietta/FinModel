"""
Excel generation module for financial statements.

This module integrates with the provider selection system to retrieve financial data
and generate Excel reports using the institutional template.
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
    """Excel report generator for financial statements."""
    
    def __init__(self, api_keys: Dict[str, str], output_dir: str = None):
        """Initialize the Excel generator.
        
        Args:
            api_keys: Dictionary of API keys for each provider.
            output_dir: Directory to save generated Excel files.
        """
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
    
    def generate_income_statement(self, ticker: str, period: str = 'quarterly', limit: int = 12) -> Optional[str]:
        """Generate Excel income statement for the specified ticker.
        
        Args:
            ticker: Ticker symbol of the company.
            period: 'quarterly' or 'annual'.
            limit: Maximum number of periods to include.
            
        Returns:
            Path to the generated Excel file, or None if generation failed.
        """
        try:
            # Normalize ticker
            ticker = ticker.strip().upper()
            
            self.logger.info(f"Generating income statement for {ticker}")
            
            # Get income statement data using provider selector
            income_statement = self.provider_selector.get_income_statement(ticker, period, limit)
            
            # Check if data was retrieved successfully
            if not income_statement or 'periods' not in income_statement or not income_statement['periods']:
                self.logger.error(f"No income statement data retrieved for {ticker}")
                return None
            
            # Generate Excel file
            output_path = os.path.join(self.output_dir, f"{ticker}_Income_Statement.xlsx")
            
            # Create Excel file using institutional template
            self.template.create_template(income_statement, output_path)
            
            self.logger.info(f"Excel income statement generated for {ticker} at {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating income statement for {ticker}: {str(e)}")
            return None
