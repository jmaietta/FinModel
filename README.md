# Financial Statement Generator - README

## Overview

This application automatically builds historical financial models for publicly-traded technology companies using quarterly financial data. The system intelligently selects the highest quality data source for each company, making the process completely transparent to the user.

## Key Features

- **Simple User Interface**: Just enter a ticker symbol to generate a detailed income statement
- **Intelligent Data Provider Selection**: Automatically selects the optimal data source based on data quality
- **Institutional-Grade Excel Output**: Comprehensive income statements with three years of quarterly history
- **Secure API Key Management**: Encrypted storage of financial data provider credentials
- **Focus on Data Accuracy**: Prioritizes the most accurate and complete financial data

## Architecture

The application consists of several key components:

1. **Provider Selection System**: Analyzes and selects the optimal data source for each request
2. **Secure API Key Manager**: Handles encrypted storage and retrieval of API credentials
3. **Excel Generator**: Creates institutional-grade Excel reports with income statement data
4. **Web Interface**: Simple, intuitive UI for entering ticker symbols and downloading reports

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd financial_web_app
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure API keys:
   - Set environment variables for your API keys:
     ```
     export POLYGON_API_KEY=your_polygon_key
     export SIMFIN_API_KEY=your_simfin_key
     export ALPHAVANTAGE_API_KEY=your_alphavantage_key
     export FINNHUB_API_KEY=your_finnhub_key
     ```
   - Or add them through the web interface after starting the application

## Usage

1. Start the application:
   ```
   python src/main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Enter a ticker symbol for any publicly-traded technology company

4. Download the generated Excel file containing the income statement

## Deployment

### Local Deployment

The application can be run locally as described in the Usage section.

### Production Deployment

For production deployment, we recommend using Gunicorn with Nginx:

1. Install Gunicorn:
   ```
   pip install gunicorn
   ```

2. Create a systemd service file (on Linux):
   ```
   [Unit]
   Description=Financial Statement Generator
   After=network.target

   [Service]
   User=<your-user>
   WorkingDirectory=/path/to/financial_web_app
   ExecStart=/path/to/financial_web_app/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 src.main:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. Configure Nginx as a reverse proxy

## API Keys

The application requires API keys for the following financial data providers:

- [Polygon.io](https://polygon.io/)
- [SimFin](https://simfin.com/)
- [Alpha Vantage](https://www.alphavantage.co/)
- [FinnHub](https://finnhub.io/)

While the application can work with keys from any of these providers, having multiple keys improves data quality and reliability.

## Customization

The Excel output format can be customized by modifying the `InstitutionalDetailedTemplate` class in the SEC parser module.

## Troubleshooting

- **API Key Issues**: Ensure your API keys are correctly entered and have appropriate permissions
- **Excel Generation Failures**: Check that the ticker symbol is valid and represents a publicly-traded company
- **Missing Data**: Some newer companies may have less than three years of quarterly data available

## License

[Specify your license here]

## Acknowledgements

This project uses the SEC parser module for financial data processing and Excel generation.
