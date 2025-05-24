"""
Data adapter module using only Polygon's Financials API for income statements.
"""
import logging
import requests
from typing import Dict, Any

class DataAdapter:
    """Abstract base for data adapters."""
    def get_income_statement(self,
                             ticker: str,
                             period: str = 'quarterly',
                             limit: int = 12) -> Dict[str, Any]:
        raise NotImplementedError

class PolygonAdapter(DataAdapter):
    """Adapter for Polygon.io Financials API focusing on the requested line items."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.polygon.io/v2/reference/financials"
        self.logger = logging.getLogger(__name__)

    def get_income_statement(self,
                             ticker: str,
                             period: str = 'quarterly',
                             limit: int = 12) -> Dict[str, Any]:
        """
        Retrieve the most recent `limit` quarters of detailed income statement metrics,
        sorted by reporting date descending.
        """
        timeframe = 'quarterly'
        try:
            url = (
                f"{self.base_url}?ticker={ticker}"
                f"&statement=ic"
                f"&timeframe={timeframe}"
                f"&limit={limit}"
                f"&sort=period_end_date"  # ensure most recent first
                f"&order=desc"
                f"&apiKey={self.api_key}"
            )
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            results = data.get('results', [])

            mapping = {
                'revenues': 'Revenues',
                'costOfRevenue': 'Cost of Goods Sold',
                'grossProfit': 'Gross Profit',
                'sellingGeneralAndAdministrativeExpense': 'Sales & Marketing Expense',
                'researchAndDevelopmentExpense': 'Research & Development Expense',
                'generalAndAdministrativeExpense': 'General & Administrative Expense',
                'depreciationAndAmortization': 'Depreciation and Amortization',
                'stockBasedCompensation': 'Stock Compensation Expense',
                'operatingIncomeLoss': 'Operating Income',
                'interestExpense': 'Interest Expense',
                'interestIncome': 'Interest Income',
                'otherExpenses': 'Other Expense',
                'otherIncome': 'Other Income',
                'incomeBeforeTax': 'Income Before Taxes',
                'incomeTaxExpense': 'Income Tax',
                'netIncome': 'Net Income',
                'weightedAverageDilutedSharesOutstanding': 'Fully Diluted Share Count',
                'epsDiluted': 'EPS (Diluted)'
            }

            statements = []
            for entry in results:
                period_end = entry.get('period_end_date')
                fin = entry.get('financials', {})
                item_values = {}
                for raw_field, label in mapping.items():
                    node = fin.get(raw_field)
                    if node and 'value' in node:
                        item_values[label] = node['value']

                statements.append({
                    'period_end_date': period_end,
                    'items': item_values
                })

            return {'ticker': ticker, 'periods': statements}

        except Exception as e:
            self.logger.error(f"Polygon income statement fetch failed for {ticker}: {e}")
            return {}
