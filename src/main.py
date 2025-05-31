"""
Main Flask application for the financial web app with rate limiting.

This module serves as the entry point for the Flask application,
integrating all components for the financial statement generator.
"""
import os
import sys
import logging
from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

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

# Initialize Excel generator
excel_generator = ExcelGenerator(api_keys)

# Block suspicious bots
@app.before_request
def block_suspicious_requests():
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Block known bot patterns that are scanning for vulnerabilities
    blocked_patterns = [
        'go-http-client',
        'python-requests/',
        'curl/',
        'wget/',
        'scanner',
        'exploit',
        'nikto',
        'sqlmap',
        'nmap'
    ]
    
    for pattern in blocked_patterns:
        if pattern in user_agent:
            logger.warning(f"Blocked suspicious request from {get_remote_address()} with UA: {user_agent}")
            abort(403)  # Forbidden

@app.route('/')
@limiter.limit("20 per minute")  # Allow 20 page loads per minute
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
@limiter.limit("5 per minute")  # Strict limit on Excel generation
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
@limiter.limit("10 per minute")  # Allow reasonable download rate
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
@limiter.limit("10 per hour")  # Very strict on API key management
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

@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt file."""
    return send_file('static/robots.txt', mimetype='text/plain')

# Rate limit error handler
@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded. Please wait a moment and try again.',
        'retry_after': e.retry_after
    }), 429

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
