"""
Enhanced Detailed Excel template module for institutional investors.

This module provides a specialized Excel template for institutional investors
with comprehensive income statement line items and three years of quarterly history.
"""
import os
import logging
from typing import Dict, List, Optional, Any
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart import LineChart, BarChart, Reference
from openpyxl.chart.series import SeriesLabel
from openpyxl.utils import get_column_letter


class InstitutionalDetailedTemplate:
    """Creates detailed Excel templates for institutional investors."""
    
    def __init__(self):
        """Initialize institutional detailed template."""
        self.logger = logging.getLogger(__name__)
        
        # Define styles
        self.header_font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
        self.subheader_font = Font(name='Arial', size=11, bold=True)
        self.normal_font = Font(name='Arial', size=10)
        self.number_font = Font(name='Arial', size=10)
        
        self.header_fill = PatternFill(start_color='0066CC', end_color='0066CC', fill_type='solid')
        self.subheader_fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')
        self.alternate_row_fill = PatternFill(start_color='F5F5F5', end_color='F5F5F5', fill_type='solid')
        
        self.center_align = Alignment(horizontal='center', vertical='center')
        self.right_align = Alignment(horizontal='right', vertical='center')
        self.left_align = Alignment(horizontal='left', vertical='center')
        
        self.border = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )
        
        # Define institutional line items in order
        self.institutional_line_items = [
            'Revenues',
            'CostOfGoodsSold',
            'GrossProfit',
            'SalesAndMarketingExpense',
            'ResearchAndDevelopmentExpense',
            'GeneralAndAdministrativeExpense',
            'StockBasedCompensation',
            'OperatingExpenses',
            'OperatingIncomeLoss',
            'InterestExpense',
            'InterestIncome',
            'OtherExpenses',
            'OtherIncome',
            'DepreciationAndAmortization',
            'IncomeLossBeforeIncomeTaxes',
            'IncomeTaxExpenseBenefit',
            'NetIncomeLoss',
            'WeightedAverageSharesOutstandingDiluted'
        ]
        
        # Map item keys to display names
        self.item_display_names = {
            'Revenues': 'Total Revenue',
            'CostOfGoodsSold': 'Cost of Goods Sold',
            'GrossProfit': 'Gross Profit',
            'SalesAndMarketingExpense': 'Sales & Marketing',
            'ResearchAndDevelopmentExpense': 'Research & Development',
            'GeneralAndAdministrativeExpense': 'General & Administrative',
            'StockBasedCompensation': 'Stock-Based Compensation',
            'OperatingExpenses': 'Total Operating Expenses',
            'OperatingIncomeLoss': 'Operating Income',
            'InterestExpense': 'Interest Expense',
            'InterestIncome': 'Interest Income',
            'OtherExpenses': 'Other Expenses',
            'OtherIncome': 'Other Income',
            'DepreciationAndAmortization': 'Depreciation & Amortization',
            'IncomeLossBeforeIncomeTaxes': 'Pre-Tax Income',
            'IncomeTaxExpenseBenefit': 'Income Tax Expense',
            'NetIncomeLoss': 'Net Income',
            'WeightedAverageSharesOutstandingDiluted': 'Fully-Diluted Shares Outstanding'
        }
    
    def create_template(self, income_statement: Dict, output_path: str) -> str:
        """Create institutional detailed template for income statement.
        
        Args:
            income_statement: Income statement data.
            output_path: Path to save the Excel file.
            
        Returns:
            Path to the saved Excel file.
        """
        wb = openpyxl.Workbook()
        
        # Create only the Income Statement sheet
        income_stmt_sheet = wb.active
        income_stmt_sheet.title = "Income Statement"
        
        # Create income statement sheet with detailed line items
        self._create_income_statement_sheet(income_stmt_sheet, income_statement)
        
        # Adjust column widths
        income_stmt_sheet.column_dimensions['A'].width = 30
        for col in range(2, 15):
            income_stmt_sheet.column_dimensions[get_column_letter(col)].width = 15
        
        # Save workbook
        try:
            wb.save(output_path)
            self.logger.info(f"Successfully saved institutional detailed template to {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"Error saving institutional detailed template: {str(e)}")
            raise
    
    def _create_income_statement_sheet(self, sheet, income_statement: Dict):
        """Create income statement sheet with institutional line items.
        
        Args:
            sheet: Excel worksheet to populate.
            income_statement: Income statement data.
        """
        # Add title
        sheet['A1'] = f"{income_statement.get('company_name', '')} ({income_statement.get('ticker', '')}) - Income Statement"
        sheet['A1'].font = Font(name='Arial', size=16, bold=True)
        sheet.merge_cells('A1:N1')
        sheet['A1'].alignment = Alignment(horizontal='center')
        
        # Extract periods and sort by date (most recent first)
        periods = income_statement.get('periods', {})
        sorted_periods = sorted(periods.items(), key=lambda x: x[0], reverse=True)
        
        if not sorted_periods:
            sheet['A3'] = "No data available"
            return
        
        # Limit to 12 quarters (3 years)
        sorted_periods = sorted_periods[:12]
        
        # Add headers
        sheet['A3'] = "Line Item"
        sheet['A3'].font = self.header_font
        sheet['A3'].fill = self.header_fill
        sheet['A3'].alignment = self.center_align
        sheet['A3'].border = self.border
        
        # Add period headers
        for i, (period_key, _) in enumerate(sorted_periods):
            col = i + 2
            cell = sheet.cell(row=3, column=col)
            cell.value = period_key
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align
            cell.border = self.border
        
        # Add line items
        for i, item_key in enumerate(self.institutional_line_items):
            row = i + 4
            
            # Item name
            cell = sheet.cell(row=row, column=1)
            cell.value = self.item_display_names.get(item_key, item_key)
            cell.font = self.normal_font
            cell.alignment = self.left_align
            cell.border = self.border
            
            # Apply alternating row fill
            if i % 2 == 1:
                cell.fill = self.alternate_row_fill
            
            # Add values for each period
            for j, (period_key, period_data) in enumerate(sorted_periods):
                col = j + 2
                cell = sheet.cell(row=row, column=col)
                
                items = period_data.get('items', {})
                if item_key in items:
                    value = items[item_key].get('value', 0)
                    cell.value = value
                    
                    # Format based on item type
                    if item_key == 'WeightedAverageSharesOutstandingDiluted':
                        cell.number_format = '#,##0'  # No currency for shares
                    else:
                        cell.number_format = '$#,##0,,"M"'  # Display in millions
                else:
                    cell.value = "N/A"
                
                cell.font = self.number_font
                cell.alignment = self.right_align
                cell.border = self.border
                
                # Apply alternating row fill
                if i % 2 == 1:
                    cell.fill = self.alternate_row_fill
        
        # Add calculated margins
        margin_items = [
            ("Gross Margin", 'GrossProfit', 'Revenues'),
            ("Operating Margin", 'OperatingIncomeLoss', 'Revenues'),
            ("Net Margin", 'NetIncomeLoss', 'Revenues')
        ]
        
        start_row = len(self.institutional_line_items) + 5
        
        # Add margin header
        cell = sheet.cell(row=start_row, column=1)
        cell.value = "Margins"
        cell.font = self.subheader_font
        cell.fill = self.subheader_fill
        cell.alignment = self.left_align
        cell.border = self.border
        
        for j in range(1, len(sorted_periods) + 2):  # Extend across all columns
            if j > 1:
                cell = sheet.cell(row=start_row, column=j)
                cell.fill = self.subheader_fill
                cell.border = self.border
        
        # Add margin calculations
        for i, (margin_name, numerator_key, denominator_key) in enumerate(margin_items):
            row = start_row + i + 1
            
            # Margin name
            cell = sheet.cell(row=row, column=1)
            cell.value = margin_name
            cell.font = self.normal_font
            cell.alignment = self.left_align
            cell.border = self.border
            
            # Apply alternating row fill
            if i % 2 == 0:
                cell.fill = self.alternate_row_fill
            
            # Calculate margin for each period
            for j, (period_key, period_data) in enumerate(sorted_periods):
                col = j + 2
                cell = sheet.cell(row=row, column=col)
                
                items = period_data.get('items', {})
                if (numerator_key in items and 
                    denominator_key in items and
                    items[denominator_key].get('value', 0) != 0):
                    
                    numerator = items[numerator_key].get('value', 0)
                    denominator = items[denominator_key].get('value', 0)
                    margin = numerator / denominator * 100
                    cell.value = margin
                    cell.number_format = '0.00"%"'
                else:
                    cell.value = "N/A"
                
                cell.font = self.number_font
                cell.alignment = self.right_align
                cell.border = self.border
                
                # Apply alternating row fill
                if i % 2 == 0:
                    cell.fill = self.alternate_row_fill
    
    def _create_quarterly_analysis_sheet(self, sheet, income_statement: Dict):
        """Create quarterly analysis sheet with QoQ growth rates.
        
        Args:
            sheet: Excel worksheet to populate.
            income_statement: Income statement data.
        """
        # Add title
        sheet['A1'] = f"{income_statement.get('company_name', '')} ({income_statement.get('ticker', '')}) - Quarterly Analysis"
        sheet['A1'].font = Font(name='Arial', size=16, bold=True)
        sheet.merge_cells('A1:N1')
        sheet['A1'].alignment = Alignment(horizontal='center')
        
        # Extract periods and sort by date (most recent first)
        periods = income_statement.get('periods', {})
        sorted_periods = sorted(periods.items(), key=lambda x: x[0], reverse=True)
        
        if not sorted_periods:
            sheet['A3'] = "No data available"
            return
        
        # Limit to 12 quarters (3 years)
        sorted_periods = sorted_periods[:12]
        
        # Add headers
        sheet['A3'] = "Line Item"
        sheet['A3'].font = self.header_font
        sheet['A3'].fill = self.header_fill
        sheet['A3'].alignment = self.center_align
        sheet['A3'].border = self.border
        
        # Add period headers for QoQ growth
        for i in range(len(sorted_periods) - 1):
            col = i + 2
            current_period = sorted_periods[i][0]
            prev_period = sorted_periods[i+1][0]
            cell = sheet.cell(row=3, column=col)
            cell.value = f"{current_period} vs {prev_period}"
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align
            cell.border = self.border
        
        # Select key metrics for QoQ analysis
        key_metrics = [
            'Revenues',
            'GrossProfit',
            'OperatingIncomeLoss',
            'NetIncomeLoss'
        ]
        
        # Add QoQ growth rates
        for i, item_key in enumerate(key_metrics):
            row = i + 4
            
            # Item name
            cell = sheet.cell(row=row, column=1)
            cell.value = self.item_display_names.get(item_key, item_key)
            cell.font = self.normal_font
            cell.alignment = self.left_align
            cell.border = self.border
            
            # Apply alternating row fill
            if i % 2 == 1:
                cell.fill = self.alternate_row_fill
            
            # Calculate QoQ growth for each period
            for j in range(len(sorted_periods) - 1):
                col = j + 2
                cell = sheet.cell(row=row, column=col)
                
                current_period_data = sorted_periods[j][1]
                prev_period_data = sorted_periods[j+1][1]
                
                current_items = current_period_data.get('items', {})
                prev_items = prev_period_data.get('items', {})
                
                if (item_key in current_items and 
                    item_key in prev_items and
                    prev_items[item_key].get('value', 0) != 0):
                    
                    current_value = current_items[item_key].get('value', 0)
                    prev_value = prev_items[item_key].get('value', 0)
                    growth = (current_value - prev_value) / prev_value * 100
                    cell.value = growth
                    cell.number_format = '0.00"%"'
                    
                    # Color code: green for positive, red for negative
                    if growth > 0:
                        cell.font = Font(name='Arial', size=10, color='006100')
                    elif growth < 0:
                        cell.font = Font(name='Arial', size=10, color='9C0006')
                    else:
                        cell.font = self.number_font
                else:
                    cell.value = "N/A"
                    cell.font = self.number_font
                
                cell.alignment = self.right_align
                cell.border = self.border
                
                # Apply alternating row fill
                if i % 2 == 1:
                    cell.fill = self.alternate_row_fill
    
    def _create_annual_analysis_sheet(self, sheet, income_statement: Dict):
        """Create annual analysis sheet with YoY growth rates.
        
        Args:
            sheet: Excel worksheet to populate.
            income_statement: Income statement data.
        """
        # Add title
        sheet['A1'] = f"{income_statement.get('company_name', '')} ({income_statement.get('ticker', '')}) - Annual Analysis"
        sheet['A1'].font = Font(name='Arial', size=16, bold=True)
        sheet.merge_cells('A1:N1')
        sheet['A1'].alignment = Alignment(horizontal='center')
        
        # Extract periods and sort by date (most recent first)
        periods = income_statement.get('periods', {})
        sorted_periods = sorted(periods.items(), key=lambda x: x[0], reverse=True)
        
        if not sorted_periods or len(sorted_periods) < 4:
            sheet['A3'] = "Insufficient data for annual analysis (need at least 4 quarters)"
            return
        
        # Limit to 12 quarters (3 years)
        sorted_periods = sorted_periods[:12]
        
        # Group periods by year
        years = {}
        for period_key, period_data in sorted_periods:
            year = period_key.split('-')[0]
            if year not in years:
                years[year] = []
            years[year].append((period_key, period_data))
        
        # Sort years in descending order
        sorted_years = sorted(years.items(), key=lambda x: x[0], reverse=True)
        
        # Add headers
        sheet['A3'] = "Line Item"
        sheet['A3'].font = self.header_font
        sheet['A3'].fill = self.header_fill
        sheet['A3'].alignment = self.center_align
        sheet['A3'].border = self.border
        
        # Add year headers
        for i, (year, _) in enumerate(sorted_years):
            col = i + 2
            cell = sheet.cell(row=3, column=col)
            cell.value = year
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align
            cell.border = self.border
        
        # Add YoY growth headers
        for i in range(len(sorted_years) - 1):
            col = i + 2 + len(sorted_years)
            current_year = sorted_years[i][0]
            prev_year = sorted_years[i+1][0]
            cell = sheet.cell(row=3, column=col)
            cell.value = f"{current_year} vs {prev_year}"
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align
            cell.border = self.border
        
        # Select key metrics for annual analysis
        key_metrics = [
            'Revenues',
            'GrossProfit',
            'OperatingIncomeLoss',
            'NetIncomeLoss'
        ]
        
        # Add annual values and YoY growth rates
        for i, item_key in enumerate(key_metrics):
            row = i + 4
            
            # Item name
            cell = sheet.cell(row=row, column=1)
            cell.value = self.item_display_names.get(item_key, item_key)
            cell.font = self.normal_font
            cell.alignment = self.left_align
            cell.border = self.border
            
            # Apply alternating row fill
            if i % 2 == 1:
                cell.fill = self.alternate_row_fill
            
            # Calculate annual values for each year
            annual_values = {}
            for j, (year, periods) in enumerate(sorted_years):
                col = j + 2
                cell = sheet.cell(row=row, column=col)
                
                # Sum values for all periods in the year
                total = 0
                count = 0
                for _, period_data in periods:
                    items = period_data.get('items', {})
                    if item_key in items:
                        total += items[item_key].get('value', 0)
                        count += 1
                
                if count > 0:
                    annual_values[year] = total
                    cell.value = total
                    cell.number_format = '$#,##0,,"M"'  # Display in millions
                else:
                    cell.value = "N/A"
                
                cell.font = self.number_font
                cell.alignment = self.right_align
                cell.border = self.border
                
                # Apply alternating row fill
                if i % 2 == 1:
                    cell.fill = self.alternate_row_fill
            
            # Calculate YoY growth rates
            for j in range(len(sorted_years) - 1):
                col = j + 2 + len(sorted_years)
                cell = sheet.cell(row=row, column=col)
                
                current_year = sorted_years[j][0]
                prev_year = sorted_years[j+1][0]
                
                if (current_year in annual_values and 
                    prev_year in annual_values and
                    annual_values[prev_year] != 0):
                    
                    current_value = annual_values[current_year]
                    prev_value = annual_values[prev_year]
                    growth = (current_value - prev_value) / prev_value * 100
                    cell.value = growth
                    cell.number_format = '0.00"%"'
                    
                    # Color code: green for positive, red for negative
                    if growth > 0:
                        cell.font = Font(name='Arial', size=10, color='006100')
                    elif growth < 0:
                        cell.font = Font(name='Arial', size=10, color='9C0006')
                    else:
                        cell.font = self.number_font
                else:
                    cell.value = "N/A"
                    cell.font = self.number_font
                
                cell.alignment = self.right_align
                cell.border = self.border
                
                # Apply alternating row fill
                if i % 2 == 1:
                    cell.fill = self.alternate_row_fill
    
    def _create_charts_sheet(self, sheet, income_statement: Dict):
        """Create charts sheet with visualizations of financial data.
        
        Args:
            sheet: Excel worksheet to populate.
            income_statement: Income statement data.
        """
        # Add title
        sheet['A1'] = f"{income_statement.get('company_name', '')} ({income_statement.get('ticker', '')}) - Financial Charts"
        sheet['A1'].font = Font(name='Arial', size=16, bold=True)
        sheet.merge_cells('A1:I1')
        sheet['A1'].alignment = Alignment(horizontal='center')
        
        # Extract periods and sort by date (oldest first for charts)
        periods = income_statement.get('periods', {})
        sorted_periods = sorted(periods.items(), key=lambda x: x[0])
        
        if not sorted_periods:
            sheet['A3'] = "No data available for charts"
            return
        
        # Limit to 12 quarters (3 years)
        if len(sorted_periods) > 12:
            sorted_periods = sorted_periods[-12:]
        
        # Create data table for charts
        sheet['A3'] = "Period"
        sheet['B3'] = "Revenue"
        sheet['C3'] = "Gross Profit"
        sheet['D3'] = "Operating Income"
        sheet['E3'] = "Net Income"
        sheet['F3'] = "Gross Margin"
        sheet['G3'] = "Operating Margin"
        sheet['H3'] = "Net Margin"
        
        # Style headers
        for col in range(1, 9):
            cell = sheet.cell(row=3, column=col)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align
            cell.border = self.border
        
        # Add data
        for i, (period_key, period_data) in enumerate(sorted_periods):
            row = i + 4
            items = period_data.get('items', {})
            
            # Period
            cell = sheet.cell(row=row, column=1)
            cell.value = period_key
            cell.font = self.normal_font
            cell.alignment = self.center_align
            cell.border = self.border
            
            # Revenue
            cell = sheet.cell(row=row, column=2)
            if 'Revenues' in items:
                cell.value = items['Revenues'].get('value', 0) / 1000000  # Convert to millions
            else:
                cell.value = None
            cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
            
            # Gross Profit
            cell = sheet.cell(row=row, column=3)
            if 'GrossProfit' in items:
                cell.value = items['GrossProfit'].get('value', 0) / 1000000  # Convert to millions
            else:
                cell.value = None
            cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
            
            # Operating Income
            cell = sheet.cell(row=row, column=4)
            if 'OperatingIncomeLoss' in items:
                cell.value = items['OperatingIncomeLoss'].get('value', 0) / 1000000  # Convert to millions
            else:
                cell.value = None
            cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
            
            # Net Income
            cell = sheet.cell(row=row, column=5)
            if 'NetIncomeLoss' in items:
                cell.value = items['NetIncomeLoss'].get('value', 0) / 1000000  # Convert to millions
            else:
                cell.value = None
            cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
            
            # Gross Margin
            cell = sheet.cell(row=row, column=6)
            if 'GrossProfit' in items and 'Revenues' in items and items['Revenues'].get('value', 0) != 0:
                gross_profit = items['GrossProfit'].get('value', 0)
                revenue = items['Revenues'].get('value', 0)
                cell.value = gross_profit / revenue * 100
            else:
                cell.value = None
            cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
            
            # Operating Margin
            cell = sheet.cell(row=row, column=7)
            if 'OperatingIncomeLoss' in items and 'Revenues' in items and items['Revenues'].get('value', 0) != 0:
                operating_income = items['OperatingIncomeLoss'].get('value', 0)
                revenue = items['Revenues'].get('value', 0)
                cell.value = operating_income / revenue * 100
            else:
                cell.value = None
            cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
            
            # Net Margin
            cell = sheet.cell(row=row, column=8)
            if 'NetIncomeLoss' in items and 'Revenues' in items and items['Revenues'].get('value', 0) != 0:
                net_income = items['NetIncomeLoss'].get('value', 0)
                revenue = items['Revenues'].get('value', 0)
                cell.value = net_income / revenue * 100
            else:
                cell.value = None
            cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
        
        # Create Revenue and Profit chart
        self._create_financial_metrics_chart(
            sheet, 
            title="Revenue and Profits",
            categories_range=f"A4:A{3+len(sorted_periods)}",
            data_ranges=[
                f"B4:B{3+len(sorted_periods)}",
                f"C4:C{3+len(sorted_periods)}",
                f"D4:D{3+len(sorted_periods)}",
                f"E4:E{3+len(sorted_periods)}"
            ],
            series_names=["Revenue", "Gross Profit", "Operating Income", "Net Income"],
            position="A15"
        )
        
        # Create Margins chart
        self._create_financial_metrics_chart(
            sheet, 
            title="Profit Margins",
            categories_range=f"A4:A{3+len(sorted_periods)}",
            data_ranges=[
                f"F4:F{3+len(sorted_periods)}",
                f"G4:G{3+len(sorted_periods)}",
                f"H4:H{3+len(sorted_periods)}"
            ],
            series_names=["Gross Margin", "Operating Margin", "Net Margin"],
            position="A30"
        )
    
    def _create_key_metrics_sheet(self, sheet, income_statement: Dict):
        """Create key metrics sheet with financial ratios and trends.
        
        Args:
            sheet: Excel worksheet to populate.
            income_statement: Income statement data.
        """
        # Add title
        sheet['A1'] = f"{income_statement.get('company_name', '')} ({income_statement.get('ticker', '')}) - Key Metrics"
        sheet['A1'].font = Font(name='Arial', size=16, bold=True)
        sheet.merge_cells('A1:E1')
        sheet['A1'].alignment = Alignment(horizontal='center')
        
        # Extract periods and sort by date (most recent first)
        periods = income_statement.get('periods', {})
        sorted_periods = sorted(periods.items(), key=lambda x: x[0], reverse=True)
        
        if not sorted_periods:
            sheet['A3'] = "No data available"
            return
        
        # Limit to 12 quarters (3 years)
        sorted_periods = sorted_periods[:12]
        
        # Add headers
        sheet['A3'] = "Metric"
        sheet['B3'] = "Most Recent"
        sheet['C3'] = "YoY Change"
        sheet['D3'] = "3Y Average"
        sheet['E3'] = "3Y CAGR"
        
        # Style headers
        for col in range(1, 6):
            cell = sheet.cell(row=3, column=col)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align
            cell.border = self.border
        
        # Get most recent period data
        most_recent_period = sorted_periods[0][1]
        most_recent_items = most_recent_period.get('items', {})
        
        # Get year-ago period if available
        year_ago_items = {}
        if len(sorted_periods) >= 4:  # Assuming quarterly data, this would be 1 year ago
            year_ago_period = sorted_periods[4][1]
            year_ago_items = year_ago_period.get('items', {})
        
        # Calculate averages
        avg_items = {}
        for item_key in ['Revenues', 'GrossProfit', 'OperatingIncomeLoss', 'NetIncomeLoss']:
            values = []
            for _, period_data in sorted_periods:  # All available quarters (up to 12)
                if item_key in period_data.get('items', {}):
                    values.append(period_data['items'][item_key].get('value', 0))
            
            if values:
                avg_items[item_key] = sum(values) / len(values)
        
        # Calculate CAGR (Compound Annual Growth Rate)
        cagr_items = {}
        for item_key in ['Revenues', 'GrossProfit', 'OperatingIncomeLoss', 'NetIncomeLoss']:
            if len(sorted_periods) >= 12:  # Need 3 years of data
                start_value = sorted_periods[-1][1].get('items', {}).get(item_key, {}).get('value', 0)
                end_value = sorted_periods[0][1].get('items', {}).get(item_key, {}).get('value', 0)
                
                if start_value > 0:
                    # Calculate CAGR: (End Value / Start Value)^(1/3) - 1
                    cagr = (end_value / start_value) ** (1/3) - 1
                    cagr_items[item_key] = cagr * 100  # Convert to percentage
        
        # Add key metrics
        metrics = [
            ("Revenue", 'Revenues'),
            ("Gross Profit", 'GrossProfit'),
            ("Operating Income", 'OperatingIncomeLoss'),
            ("Net Income", 'NetIncomeLoss')
        ]
        
        for i, (metric_name, metric_key) in enumerate(metrics):
            row = i + 4
            
            # Metric name
            cell = sheet.cell(row=row, column=1)
            cell.value = metric_name
            cell.font = self.normal_font
            cell.alignment = self.left_align
            cell.border = self.border
            
            # Most recent value
            cell = sheet.cell(row=row, column=2)
            if metric_key in most_recent_items:
                value = most_recent_items[metric_key].get('value', 0)
                cell.value = value / 1000000  # Convert to millions
                cell.number_format = '$#,##0.00 "M"'
            else:
                cell.value = "N/A"
            cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
            
            # YoY change
            cell = sheet.cell(row=row, column=3)
            if metric_key in most_recent_items and metric_key in year_ago_items:
                current = most_recent_items[metric_key].get('value', 0)
                year_ago = year_ago_items[metric_key].get('value', 0)
                if year_ago != 0:
                    change = (current - year_ago) / year_ago * 100
                    cell.value = change
                    cell.number_format = '0.00"%"'
                    
                    # Color code: green for positive, red for negative
                    if change > 0:
                        cell.font = Font(name='Arial', size=10, color='006100')
                    elif change < 0:
                        cell.font = Font(name='Arial', size=10, color='9C0006')
                else:
                    cell.value = "N/A"
                    cell.font = self.number_font
            else:
                cell.value = "N/A"
                cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
            
            # 3Y average
            cell = sheet.cell(row=row, column=4)
            if metric_key in avg_items:
                cell.value = avg_items[metric_key] / 1000000  # Convert to millions
                cell.number_format = '$#,##0.00 "M"'
            else:
                cell.value = "N/A"
            cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
            
            # 3Y CAGR
            cell = sheet.cell(row=row, column=5)
            if metric_key in cagr_items:
                cell.value = cagr_items[metric_key]
                cell.number_format = '0.00"%"'
                
                # Color code: green for positive, red for negative
                if cagr_items[metric_key] > 0:
                    cell.font = Font(name='Arial', size=10, color='006100')
                elif cagr_items[metric_key] < 0:
                    cell.font = Font(name='Arial', size=10, color='9C0006')
            else:
                cell.value = "N/A"
                cell.font = self.number_font
            cell.alignment = self.right_align
            cell.border = self.border
    
    def _create_financial_metrics_chart(self, sheet, title, categories_range, data_ranges, series_names, position):
        """Create a line chart for financial metrics.
        
        Args:
            sheet: Excel worksheet to add the chart to.
            title: Chart title.
            categories_range: Range for category labels (periods).
            data_ranges: List of ranges for data series.
            series_names: List of names for data series.
            position: Cell position for the chart.
        """
        chart = LineChart()
        chart.title = title
        chart.style = 2
        chart.height = 15  # Height in centimeters
        chart.width = 25   # Width in centimeters
        
        # Add categories (periods)
        cats = Reference(sheet, range_string=f"{sheet.title}!{categories_range}")
        chart.set_categories(cats)
        
        # Add data series
        for i, (data_range, series_name) in enumerate(zip(data_ranges, series_names)):
            data = Reference(sheet, range_string=f"{sheet.title}!{data_range}")
            
            if i >= len(chart.series):
                chart.add_data(data, titles_from_data=False)
                series = chart.series[i]
            else:
                series = chart.series[i]
                series.values = data
            
            # Set series title using SeriesLabel
            series.tx = SeriesLabel(v=series_name)
        
        # Add the chart to the worksheet
        sheet.add_chart(chart, position)
