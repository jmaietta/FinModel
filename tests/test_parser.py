"""
Test script for the SEC EDGAR Parser.

This script tests the parser on real SEC filings to ensure it works correctly.
"""
import os
import sys
import logging
import json
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.main import SecParserApp


def setup_logging():
    """Set up logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def test_apple_filings():
    """Test parsing Apple (AAPL) filings."""
    logger = logging.getLogger(__name__)
    logger.info("Testing parser on Apple (AAPL) filings")
    
    # Initialize the application
    app = SecParserApp()
    
    # Set date range for the last 2 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)
    
    # Parse Apple filings
    results = app.parse_company(
        ticker='AAPL',
        form_types=['10-K', '10-Q'],
        start_date=start_date,
        end_date=end_date,
        limit=3
    )
    
    logger.info(f"Processed {len(results)} filings for AAPL")
    
    # Check results
    for i, result in enumerate(results):
        logger.info(f"Result {i+1}:")
        logger.info(f"  Filing: {result.get('filing_info', {}).get('form_type')} - {result.get('filing_info', {}).get('filing_date')}")
        logger.info(f"  Validation: {'Valid' if result.get('validation', {}).get('valid', False) else 'Invalid'}")
        
        # Count issues and warnings
        issues = result.get('validation', {}).get('issues', [])
        warnings = result.get('validation', {}).get('warnings', [])
        logger.info(f"  Issues: {len(issues)}")
        logger.info(f"  Warnings: {len(warnings)}")
        
        # Count income statement periods
        periods = result.get('income_statement', {})
        logger.info(f"  Periods: {len(periods)}")
        
        # Check for key metrics in the first period
        if periods:
            first_period_key = list(periods.keys())[0]
            first_period = periods[first_period_key]
            items = first_period.get('items', {})
            
            key_metrics = [
                'Revenues',
                'GrossProfit',
                'OperatingIncomeLoss',
                'NetIncomeLoss'
            ]
            
            for metric in key_metrics:
                if metric in items:
                    logger.info(f"  {metric}: {items[metric].get('value')}")
                else:
                    logger.info(f"  {metric}: Not found")


def test_tech_companies():
    """Test parsing multiple technology companies."""
    logger = logging.getLogger(__name__)
    logger.info("Testing parser on multiple technology companies")
    
    # Initialize the application
    app = SecParserApp()
    
    # Test a list of tech companies
    tech_companies = ['MSFT', 'GOOGL', 'META', 'NVDA', 'INTC']
    
    for ticker in tech_companies:
        logger.info(f"Testing {ticker}")
        
        # Parse the most recent 10-K
        results = app.parse_company(
            ticker=ticker,
            form_types=['10-K'],
            limit=1
        )
        
        if results:
            result = results[0]
            logger.info(f"  Filing: {result.get('filing_info', {}).get('form_type')} - {result.get('filing_info', {}).get('filing_date')}")
            logger.info(f"  Validation: {'Valid' if result.get('validation', {}).get('valid', False) else 'Invalid'}")
            
            # Count issues and warnings
            issues = result.get('validation', {}).get('issues', [])
            warnings = result.get('validation', {}).get('warnings', [])
            logger.info(f"  Issues: {len(issues)}")
            logger.info(f"  Warnings: {len(warnings)}")
            
            # Count income statement periods
            periods = result.get('income_statement', {})
            logger.info(f"  Periods: {len(periods)}")
        else:
            logger.warning(f"  No results for {ticker}")


def test_sector_parsing():
    """Test parsing the entire Technology sector."""
    logger = logging.getLogger(__name__)
    logger.info("Testing parser on Technology sector")
    
    # Initialize the application
    app = SecParserApp()
    
    # Parse tech sector filings
    results = app.parse_tech_sector(
        form_types=['10-K'],
        limit_per_company=1,
        total_limit=10
    )
    
    logger.info(f"Processed {len(results)} filings for Technology sector")
    
    # Group results by company
    companies = {}
    for result in results:
        ticker = result.get('filing_info', {}).get('ticker')
        if ticker not in companies:
            companies[ticker] = []
        companies[ticker].append(result)
    
    logger.info(f"Found data for {len(companies)} companies")
    
    # Check results for each company
    for ticker, company_results in companies.items():
        logger.info(f"Company: {ticker}")
        logger.info(f"  Filings: {len(company_results)}")
        
        for i, result in enumerate(company_results):
            logger.info(f"  Filing {i+1}: {result.get('filing_info', {}).get('form_type')} - {result.get('filing_info', {}).get('filing_date')}")
            logger.info(f"    Validation: {'Valid' if result.get('validation', {}).get('valid', False) else 'Invalid'}")
            
            # Count income statement periods
            periods = result.get('income_statement', {})
            logger.info(f"    Periods: {len(periods)}")


def main():
    """Main entry point for the test script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting SEC EDGAR Parser tests")
    
    # Run tests
    test_apple_filings()
    test_tech_companies()
    test_sector_parsing()
    
    logger.info("All tests completed")


if __name__ == '__main__':
    main()
