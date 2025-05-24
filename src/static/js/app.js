"""
JavaScript for the financial statement generator web application.

This script handles the user interface interactions and API calls
for the financial statement generator.
"""
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const tickerForm = document.getElementById('ticker-form');
    const loadingSection = document.getElementById('loading-section');
    const resultSection = document.getElementById('result-section');
    const resultCompany = document.getElementById('result-company');
    const downloadLink = document.getElementById('download-link');
    const newSearchBtn = document.getElementById('new-search');
    
    // Form submission handler
    tickerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const ticker = document.getElementById('ticker').value.trim().toUpperCase();
        
        if (ticker) {
            // Show loading
            loadingSection.style.display = 'block';
            resultSection.style.display = 'none';
            
            // Call API to generate report
            fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ticker: ticker }),
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading
                loadingSection.style.display = 'none';
                
                if (data.success) {
                    // Update result and show result section
                    resultCompany.textContent = `${ticker} Income Statement`;
                    downloadLink.href = data.download_url;
                    resultSection.style.display = 'block';
                } else {
                    // Show error
                    alert(`Error: ${data.error || 'Failed to generate report'}`);
                }
            })
            .catch(error => {
                // Hide loading and show error
                loadingSection.style.display = 'none';
                alert(`Error: ${error.message || 'An unexpected error occurred'}`);
            });
        }
    });
    
    // New search button handler
    newSearchBtn.addEventListener('click', function() {
        resultSection.style.display = 'none';
        document.getElementById('ticker').value = '';
    });
});
