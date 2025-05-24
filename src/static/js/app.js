// Ensure the file is saved without a BOM or stray characters
document.addEventListener('DOMContentLoaded', function() {
  const tickerForm     = document.getElementById('ticker-form');
  const loadingSection = document.getElementById('loading-section');
  const resultSection  = document.getElementById('result-section');
  const resultCompany  = document.getElementById('result-company');
  const downloadLink   = document.getElementById('download-link');
  const newSearchBtn   = document.getElementById('new-search');

  tickerForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const ticker = document.getElementById('ticker')
                        .value
                        .trim()
                        .toUpperCase();
    if (!ticker) return;

    // Show loading, hide previous result
    loadingSection.style.display = 'block';
    resultSection.style.display  = 'none';

    fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker })
    })
    .then(response => response.json())
    .then(data => {
      loadingSection.style.display = 'none';
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
      alert('Error: ' + err.message);
    });
  });

  newSearchBtn.addEventListener('click', function() {
    resultSection.style.display = 'none';
    document.getElementById('ticker').value = '';
  });
});
