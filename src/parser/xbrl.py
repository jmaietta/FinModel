"""
XBRL parser module for extracting financial data from XBRL documents.

This module provides functionality for parsing XBRL documents
and extracting structured financial data.
"""
import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Union, Any


class XbrlParser:
    """Parses XBRL documents to extract financial data."""
    
    def __init__(self):
        """Initialize XBRL parser."""
        self.logger = logging.getLogger(__name__)
        
        # Common namespaces in XBRL documents
        self.namespaces = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'us-gaap': 'http://fasb.org/us-gaap/2021',
            'dei': 'http://xbrl.sec.gov/dei/2021',
            'link': 'http://www.xbrl.org/2003/linkbase',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
    
    def parse_income_statement(self, xbrl_path: str) -> Dict:
        """Parse income statement data from an XBRL document.
        
        Args:
            xbrl_path: Path to the XBRL document.
            
        Returns:
            Parsed income statement data.
        """
        self.logger.info(f"Parsing income statement from XBRL: {xbrl_path}")
        
        # This is a simplified implementation
        # In a real-world scenario, we would use a more robust XBRL parser
        
        result = {
            'ticker': '',
            'company_name': '',
            'periods': {}
        }
        
        try:
            # Parse XML
            tree = ET.parse(xbrl_path)
            root = tree.getroot()
            
            # Extract company information
            result['ticker'] = self._extract_ticker(root)
            result['company_name'] = self._extract_company_name(root)
            
            # Extract contexts (periods)
            contexts = self._extract_contexts(root)
            
            # Extract income statement items
            income_stmt_items = self._extract_income_statement_items(root, contexts)
            
            # Organize by period
            for context_id, context_info in contexts.items():
                period_key = context_info.get('period_end', '')
                if not period_key:
                    continue
                
                # Initialize period data
                if period_key not in result['periods']:
                    result['periods'][period_key] = {
                        'period_end_date': period_key,
                        'period_type': context_info.get('period_type', ''),
                        'currency': 'USD',  # Default currency
                        'items': {}
                    }
                
                # Add items for this period
                for item_key, item_data in income_stmt_items.items():
                    if context_id in item_data:
                        result['periods'][period_key]['items'][item_key] = {
                            'value': item_data[context_id].get('value', 0),
                            'unit': item_data[context_id].get('unit', '')
                        }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing XBRL document: {str(e)}")
            return result
    
    def _extract_ticker(self, root: ET.Element) -> str:
        """Extract ticker symbol from XBRL document.
        
        Args:
            root: Root element of the XBRL document.
            
        Returns:
            Ticker symbol.
        """
        # Look for ticker in dei:TradingSymbol
        ticker_elements = root.findall('.//dei:TradingSymbol', self.namespaces)
        if ticker_elements:
            return ticker_elements[0].text or ''
        
        return ''
    
    def _extract_company_name(self, root: ET.Element) -> str:
        """Extract company name from XBRL document.
        
        Args:
            root: Root element of the XBRL document.
            
        Returns:
            Company name.
        """
        # Look for company name in dei:EntityRegistrantName
        name_elements = root.findall('.//dei:EntityRegistrantName', self.namespaces)
        if name_elements:
            return name_elements[0].text or ''
        
        return ''
    
    def _extract_contexts(self, root: ET.Element) -> Dict:
        """Extract contexts from XBRL document.
        
        Args:
            root: Root element of the XBRL document.
            
        Returns:
            Dictionary mapping context IDs to context information.
        """
        contexts = {}
        
        # Find all context elements
        context_elements = root.findall('.//xbrli:context', self.namespaces)
        
        for context in context_elements:
            context_id = context.get('id', '')
            if not context_id:
                continue
            
            # Extract period information
            period = context.find('.//xbrli:period', self.namespaces)
            if period is None:
                continue
            
            # Check if instant or duration
            instant = period.find('.//xbrli:instant', self.namespaces)
            start_date = period.find('.//xbrli:startDate', self.namespaces)
            end_date = period.find('.//xbrli:endDate', self.namespaces)
            
            if instant is not None:
                period_end = instant.text
                period_type = 'instant'
            elif end_date is not None:
                period_end = end_date.text
                period_type = 'duration'
                if start_date is not None:
                    period_start = start_date.text
                else:
                    period_start = ''
            else:
                continue
            
            # Check if this is a quarterly or annual context
            if period_type == 'duration':
                # This is a simplified heuristic
                # In a real-world scenario, we would use more robust logic
                if 'Q' in context_id or 'q' in context_id:
                    period_type = 'quarterly'
                else:
                    period_type = 'annual'
            
            # Add to contexts dictionary
            contexts[context_id] = {
                'period_end': period_end,
                'period_type': period_type
            }
            
            if period_type == 'duration':
                contexts[context_id]['period_start'] = period_start
        
        return contexts
    
    def _extract_income_statement_items(self, root: ET.Element, contexts: Dict) -> Dict:
        """Extract income statement items from XBRL document.
        
        Args:
            root: Root element of the XBRL document.
            contexts: Dictionary mapping context IDs to context information.
            
        Returns:
            Dictionary mapping item names to values by context.
        """
        items = {}
        
        # Common income statement concepts in US GAAP taxonomy
        income_stmt_concepts = [
            'Revenues',
            'Revenue',
            'SalesRevenueNet',
            'CostOfRevenue',
            'GrossProfit',
            'OperatingExpenses',
            'OperatingIncomeLoss',
            'IncomeLossFromContinuingOperationsBeforeIncomeTaxes',
            'IncomeTaxExpenseBenefit',
            'NetIncomeLoss',
            'EarningsPerShareBasic',
            'EarningsPerShareDiluted'
        ]
        
        # Find all elements with these concepts
        for concept in income_stmt_concepts:
            # Try with us-gaap namespace
            elements = root.findall(f'.//us-gaap:{concept}', self.namespaces)
            
            for element in elements:
                context_ref = element.get('contextRef', '')
                if not context_ref or context_ref not in contexts:
                    continue
                
                # Get value and unit
                value_text = element.text
                if not value_text:
                    continue
                
                try:
                    value = float(value_text)
                except ValueError:
                    continue
                
                # Get unit
                unit_ref = element.get('unitRef', '')
                unit = 'USD'  # Default unit
                
                # Initialize item in dictionary
                if concept not in items:
                    items[concept] = {}
                
                # Add value for this context
                items[concept][context_ref] = {
                    'value': value,
                    'unit': unit
                }
        
        return items
