"""
Test script for validating the SEC EDGAR Parser with local data.

This script tests the parser's ability to extract and process income statement data
from local files, ensuring the hybrid adapter approach works correctly.
"""
import os
import sys
import logging
import json
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.adapter.data_adapter import LocalFileAdapter, AdapterFactory
from src.normalizer.data import IncomeStatementNormalizer
from src.validator.engine import DataValidator


def setup_logging():
    """Set up logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def test_local_adapter():
    """Test the local file adapter with sample data."""
    logger = logging.getLogger(__name__)
    logger.info("Testing local file adapter with sample data")
    
    # Initialize the local adapter
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    adapter = LocalFileAdapter(data_dir)
    
    # Test with Apple data
    ticker = 'AAPL'
    logger.info(f"Testing with {ticker} data")
    
    # Get income statement data
    income_statement = adapter.get_income_statement(ticker, period='quarterly', limit=5)
    
    if not income_statement or not income_statement.get('periods'):
        logger.error(f"No income statement data found for {ticker}")
        return
    
    # Log basic information
    logger.info(f"Found income statement data for {income_statement.get('company_name', ticker)}")
    logger.info(f"Number of periods: {len(income_statement.get('periods', {}))}")
    
    # Check for key metrics in each period
    for period_key, period_data in income_statement.get('periods', {}).items():
        logger.info(f"Period: {period_key}")
        
        items = period_data.get('items', {})
        key_metrics = [
            'Revenues',
            'GrossProfit',
            'OperatingIncomeLoss',
            'NetIncomeLoss'
        ]
        
        for metric in key_metrics:
            if metric in items:
                value = items[metric].get('value')
                unit = items[metric].get('unit')
                logger.info(f"  {metric}: {value} {unit}")
            else:
                logger.warning(f"  {metric}: Not found")
    
    # Validate the data structure
    validator = DataValidator()
    validation_result = validator.validate_income_statement(income_statement)
    
    logger.info(f"Validation result: {'Valid' if validation_result.get('valid') else 'Invalid'}")
    if not validation_result.get('valid'):
        logger.error(f"Validation issues: {validation_result.get('issues')}")
    
    # Test normalization
    normalizer = IncomeStatementNormalizer()
    normalized_data = normalizer.normalize(income_statement)
    
    logger.info("Normalized data:")
    logger.info(f"  Revenue growth metrics: {len(normalized_data.get('metrics', {}).get('revenue_growth', []))}")
    logger.info(f"  Profit margin metrics: {len(normalized_data.get('metrics', {}).get('profit_margins', []))}")
    
    # Save normalized data to file
    output_file = os.path.join(data_dir, f"{ticker}_normalized.json")
    with open(output_file, 'w') as f:
        json.dump(normalized_data, f, indent=2)
    
    logger.info(f"Saved normalized data to {output_file}")


def test_adapter_factory():
    """Test the adapter factory with different configurations."""
    logger = logging.getLogger(__name__)
    logger.info("Testing adapter factory")
    
    # Test local adapter
    local_config = {
        'data_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    }
    
    try:
        local_adapter = AdapterFactory.create_adapter('local', local_config)
        logger.info("Successfully created local adapter")
        
        # Test with sample data
        ticker = 'AAPL'
        income_statement = local_adapter.get_income_statement(ticker)
        
        if income_statement and income_statement.get('periods'):
            logger.info(f"Local adapter successfully retrieved {len(income_statement.get('periods', {}))} periods for {ticker}")
        else:
            logger.warning(f"Local adapter could not retrieve data for {ticker}")
    
    except Exception as e:
        logger.error(f"Error creating or using local adapter: {str(e)}")
    
    # Test other adapter types (these will fail without API keys, which is expected)
    adapter_types = ['polygon', 'simfin', 'alphavantage', 'finnhub']
    
    for adapter_type in adapter_types:
        try:
            # Create with empty API key (will fail when used, but should create)
            adapter = AdapterFactory.create_adapter(adapter_type, {'api_key': ''})
            logger.info(f"Successfully created {adapter_type} adapter")
        except Exception as e:
            logger.error(f"Error creating {adapter_type} adapter: {str(e)}")


def main():
    """Main entry point for the test script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting SEC EDGAR Parser validation tests")
    
    # Run tests
    test_local_adapter()
    test_adapter_factory()
    
    logger.info("All validation tests completed")


if __name__ == '__main__':
    main()
