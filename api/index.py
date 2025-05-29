"""
Vercel entry point for Flask application.
"""
import sys
import os

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing Flask app
from src.main import app

# Export for Vercel
def application(environ, start_response):
    return app.wsgi_app(environ, start_response)

# For local development
if __name__ == "__main__":
    app.run(debug=True)
