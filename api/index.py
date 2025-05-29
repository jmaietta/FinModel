# Force rebuild v3
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>FinModel - Test</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            .container { max-width: 500px; margin: 0 auto; }
            h1 { color: #0066cc; }
            .status { padding: 20px; background: #e8f5e9; border-radius: 8px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 FinModel is Working!</h1>
            <div class="status">
                <h3>✅ Deployment Successful</h3>
                <p>Your Vercel deployment is now working correctly.</p>
            </div>
            <p><strong>Next:</strong> We'll add the Excel generation feature.</p>
        </div>
    </body>
    </html>
    '''

# This is required for Vercel
def handler(request):
    return app(request.environ, lambda *args: None)
