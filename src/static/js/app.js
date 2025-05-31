// Updated app.js with rate limit handling
document.addEventListener('DOMContentLoaded', function() {
  const tickerForm     = document.getElementById('ticker-form');
  const loadingSection = document.getElementById('loading-section');
  const resultSection  = document.getElementById('result-section');
  const resultCompany  = document.getElementById('result-company');
  const downloadLink   = document.getElementById('download-link');
  const newSearchBtn   = document.getElementById('new-search');

  // Track if we're currently processing a request
  let isProcessing = false;

  tickerForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Prevent double submissions
    if (isProcessing) {
      return;
    }
    
    const ticker = document.getElementById('ticker')
                        .value
                        .trim()
                        .toUpperCase();
    if (!ticker) return;

    // Set processing state
    isProcessing = true;
    
    // Show loading, hide previous result
    loadingSection.style.display = 'block';
    resultSection.style.display  = 'none';

    fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker })
    })
    .then(response => {
      // Handle rate limiting
      if (response.status === 429) {
        return response.json().then(data => {
          throw new Error(`Rate limit exceeded. Please wait ${data.retry_after || 60} seconds and try again.`);
        });
      }
      return response.json();
    })
    .then(data => {
      loadingSection.style.display = 'none';
      isProcessing = false;
      
      if (data.success) {
        resultCompany.textContent    = `${ticker} Income Statement`;
        downloadLink.href            = data.download_url;
        resultSection.style.display  = 'block';
      } else {
        alert('Error: ' + (data.error || 'Failed to generate report'));
      }
    })
    .catch(err => {
      loadingSection.style.display = 'none';
      isProcessing = false;
      
      // Show user-friendly error message
      if (err.message.includes('Rate limit')) {
        alert(err.message);
      } else {
        alert('Error: ' + err.message);
      }
    });
  });

  newSearchBtn.addEventListener('click', function() {
    resultSection.style.display = 'none';
    document.getElementById('ticker').value = '';
    isProcessing = false; // Reset processing state
  });
});
