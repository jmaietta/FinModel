"""
Main Flask application for the financial web app.

This module serves as the entry point for the Flask application,
integrating all components for the financial statement generator.
"""
import os
import sys
import logging
from flask import Flask, render_template, request, jsonify, send_file, abort
import tempfile

import os
from flask import send_file, abort

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import application modules
from src.api_key_manager import ApiKeyManager
from src.excel_generator import ExcelGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()

# Initialize API key manager
api_key_manager = ApiKeyManager()
api_key_manager.initialize_encryption(app.config['SECRET_KEY'])

# Load API keys (or use environment variables as fallback)
api_keys = api_key_manager.get_api_keys()
if not api_keys:
    # Fallback to environment variables
    api_keys = {
        'polygon': os.environ.get('POLYGON_API_KEY', ''),
        'simfin': os.environ.get('SIMFIN_API_KEY', ''),
        'alphavantage': os.environ.get('ALPHAVANTAGE_API_KEY', ''),
        'finnhub': os.environ.get('FINNHUB_API_KEY', '')
    }
    # Store keys if any are found
    if any(api_keys.values()):
        api_key_manager.store_api_keys(api_keys)

# Vercel-specific: Use temporary directory for file operations  
TEMP_DIR = '/tmp' if os.path.exists('/tmp') else tempfile.gettempdir()
excel_generator = ExcelGenerator(api_keys, output_dir=TEMP_DIR)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_report():
    """Generate financial report for the specified ticker."""
    data = request.json
    ticker = data.get('ticker', '').strip().upper()
    
    if not ticker:
        return jsonify({'success': False, 'error': 'Ticker symbol is required'}), 400
    
    try:
        # Generate Excel file
        output_path = excel_generator.generate_income_statement(ticker)
        
        if output_path and os.path.exists(output_path):
            # Return success with download URL
            return jsonify({
                'success': True,
                'ticker': ticker,
                'download_url': f'/api/download/{ticker}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to generate income statement for {ticker}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error generating report for {ticker}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download/<ticker>')
def download_report(ticker):
    """Download the generated Excel file."""
    ticker = ticker.strip().upper()
    file_path = os.path.join(excel_generator.output_dir, f"{ticker}_Income_Statement.xlsx")
    
    if os.path.exists(file_path):
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{ticker}_Income_Statement.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        abort(404)

@app.route('/api/keys', methods=['GET', 'POST'])
def manage_api_keys():
    """Manage API keys."""
    if request.method == 'GET':
        # Return masked API keys (for UI display)
        masked_keys = {}
        for provider, key in api_key_manager.get_api_keys().items():
            if key:
                # Mask all but last 4 characters
                masked_keys[provider] = '•' * (len(key) - 4) + key[-4:] if len(key) > 4 else '•' * len(key)
            else:
                masked_keys[provider] = ''
        
        return jsonify({'success': True, 'keys': masked_keys})
    
    elif request.method == 'POST':
        # Update API keys
        data = request.json
        api_keys = data.get('keys', {})
        
        if api_key_manager.store_api_keys(api_keys):
            # Reinitialize Excel generator with new keys
            global excel_generator
            excel_generator = ExcelGenerator(api_keys)
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to store API keys'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
