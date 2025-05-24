# SEC EDGAR Parser Research Findings

## Overview
This document summarizes the research findings on SEC EDGAR data formats and best practices for extracting income statements from SEC filings (8-K, 10-Q, and 10-K) for publicly-traded Technology companies.

## SEC EDGAR Data Formats

### XBRL Format
- eXtensible Business Reporting Language (XBRL) is the standard format required by the SEC for financial reporting
- XBRL uses taxonomies to define financial concepts and their relationships
- US GAAP Taxonomy is the primary taxonomy used for financial reporting in the US
- Companies can create custom extensions to the standard taxonomy for company-specific reporting needs
- XBRL data is structured as "facts" with context information (reporting period, entity, etc.)

### Filing Types
- **10-K**: Annual reports containing comprehensive financial statements
- **10-Q**: Quarterly reports with less detailed financial information than 10-K
- **8-K**: Current reports for significant events, may contain updated financial information

### Income Statement Representation
- Income statements in XBRL are organized using specific taxonomy elements
- Key income statement concepts include Revenue, Cost of Revenue, Gross Profit, Operating Expenses, Operating Income, and Net Income
- Different companies may use different taxonomies or extensions for the same financial concepts
- Technology sector companies often have specific line items related to R&D, technology licensing, etc.

## Best Practices for Extraction

### 1. SEC API Access
- Use the SEC's EDGAR API for programmatic access to filings
- Alternative commercial APIs (sec-api.io, etc.) provide more user-friendly interfaces and pre-processed data
- Implement rate limiting and backoff strategies to comply with SEC's fair access policies

### 2. Company Identification
- Use Central Index Key (CIK) as the primary identifier for companies
- Map ticker symbols to CIK numbers for user-friendly access
- Filter companies by Standard Industrial Classification (SIC) codes to identify Technology sector companies
  - Technology sector SIC codes: 7370-7379 (Computer Programming, Data Processing), 3570-3579 (Computer Equipment), etc.

### 3. Filing Identification and Retrieval
- Use the SEC's directory structure to locate filings by company and date
- Implement filtering by form type (10-K, 10-Q, 8-K) and date range
- Extract the XBRL instance document from the filing package

### 4. XBRL Parsing Strategies
- Use specialized XBRL parsers or libraries to handle the complex XML structure
- Extract both the instance document and the company-specific taxonomy extensions
- Map custom taxonomy elements to standard US GAAP concepts
- Handle inline XBRL (iXBRL) which embeds XBRL tags in HTML documents

### 5. Income Statement Extraction
- Identify income statement sections using role references in the presentation linkbase
- Look for specific taxonomy elements that indicate income statement items
- Handle different time periods (quarterly, year-to-date, annual)
- Normalize data across different reporting periods for consistent comparison

### 6. Handling Company-Specific Extensions
- Create a mapping system between custom extensions and standard concepts
- Use semantic analysis to match custom elements to standard elements
- Maintain a growing database of known mappings to improve future parsing

### 7. Data Normalization
- Standardize units of measurement (typically USD)
- Handle scaling factors (thousands, millions, billions)
- Normalize reporting periods to enable quarter-to-quarter comparison
- Handle restatements and adjustments to previous periods

### 8. Technology Sector Specifics
- Pay special attention to R&D expenses, which are significant in tech companies
- Handle subscription revenue recognition, which is common in SaaS companies
- Account for stock-based compensation, which is prevalent in tech companies
- Extract segment information for companies with multiple business lines

## Challenges and Solutions

### Challenge 1: Inconsistent Taxonomy Usage
- **Solution**: Implement a flexible mapping system that can handle variations in taxonomy usage
- **Solution**: Use machine learning to improve mapping accuracy over time

### Challenge 2: Historical Data Format Changes
- **Solution**: Implement version-specific parsers for different EDGAR filing formats
- **Solution**: Handle both XBRL and pre-XBRL formats for comprehensive historical coverage

### Challenge 3: Complex Nested Structures
- **Solution**: Use recursive parsing strategies to handle nested XBRL elements
- **Solution**: Implement context-aware parsing to understand the hierarchical relationships

### Challenge 4: Performance with Large Datasets
- **Solution**: Implement incremental processing for large filings
- **Solution**: Use parallel processing for batch extraction of multiple filings

## Implementation Recommendations

1. **Modular Architecture**: Separate concerns for filing retrieval, XBRL parsing, and data normalization
2. **Extensible Design**: Allow for easy addition of new taxonomy mappings and company-specific rules
3. **Caching Strategy**: Cache processed results to avoid redundant processing of the same filings
4. **Validation Framework**: Implement comprehensive validation to ensure data accuracy
5. **Error Handling**: Robust error handling for unexpected filing formats or missing data
6. **Documentation**: Thorough documentation of mapping decisions and normalization rules

## Next Steps
Based on this research, the next step is to design a parser architecture that incorporates these best practices and addresses the specific requirements for extracting income statements from Technology sector companies.
