// Utility functions
function downloadFrom(url) {
    return fetch(url)
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || 'Download failed');
                });
            }
            
            // Get filename from Content-Disposition header or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'download';
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
                if (filenameMatch) {
                    filename = filenameMatch[1];
                }
            }
            
            return response.blob().then(blob => {
                // Create temporary download link
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                return { success: true, filename };
            });
        });
}

function withStatus(button, promise) {
    const btnText = button.querySelector('.btn-text');
    const btnSpinner = button.querySelector('.btn-spinner');
    const originalText = btnText.textContent;
    
    // Disable button and show spinner
    button.disabled = true;
    btnText.style.display = 'none';
    btnSpinner.style.display = 'inline';
    
    return promise
        .then(result => {
            // Show success state
            button.classList.add('success');
            btnText.textContent = 'Saved!';
            btnText.style.display = 'inline';
            btnSpinner.style.display = 'none';
            
            // Reset after 2 seconds
            setTimeout(() => {
                button.classList.remove('success');
                btnText.textContent = originalText;
                button.disabled = false;
            }, 2000);
            
            return result;
        })
        .catch(error => {
            // Reset button state
            button.disabled = false;
            btnText.textContent = originalText;
            btnText.style.display = 'inline';
            btnSpinner.style.display = 'none';
            
            // Show error toast
            showToast(error.message || 'An error occurred');
            throw error;
        });
}

function saveToDatabase(url) {
    // Show progress container
    const progressContainer = document.getElementById('progress-container');
    const progressFill = document.getElementById('progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressMessage = document.getElementById('progress-message');
    const progressDetails = document.getElementById('progress-details');
    
    progressContainer.style.display = 'block';
    
    // Start listening to Server-Sent Events for progress
    const eventSource = new EventSource('/api/progress');
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // Update progress display
        progressFill.style.width = data.progress + '%';
        progressPercentage.textContent = data.progress + '%';
        progressMessage.textContent = data.message;
        
        // Update details if available
        if (data.details && Object.keys(data.details).length > 0) {
            let detailsText = '';
            if (data.details.records_count) {
                detailsText += `Records: ${data.details.records_count} `;
            }
            if (data.details.current_sector) {
                detailsText += `Sector: ${data.details.current_sector} `;
            }
            if (data.details.trade_date) {
                detailsText += `Date: ${data.details.trade_date} `;
            }
            progressDetails.textContent = detailsText;
        } else {
            progressDetails.textContent = '';
        }
        
        // Close event source when done
        if (data.status === 'completed' || data.status === 'error') {
            eventSource.close();
            
            // Hide progress after 3 seconds if successful
            if (data.status === 'completed') {
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                }, 3000);
            }
        }
    };
    
    eventSource.onerror = function(event) {
        console.error('SSE Error:', event);
        eventSource.close();
    };
    
    // Start the actual database save operation
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                eventSource.close();
                progressContainer.style.display = 'none';
                throw new Error(err.detail?.message || err.detail?.error || 'Database save failed');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Database save successful:', data);
            return { success: true, data };
        } else {
            console.warn('Partial success:', data);
            return { success: false, data };
        }
    })
    .catch(error => {
        eventSource.close();
        progressContainer.style.display = 'none';
        throw error;
    });
}

// Toast notification system
function showToast(message) {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    // Remove toast after 4 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 4000);
}

// Build URL with query parameters
function buildUrl(baseUrl, params = {}) {
    const url = new URL(baseUrl, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
            url.searchParams.append(key, value);
        }
    });
    return url.toString();
}

// Event handlers
document.addEventListener('DOMContentLoaded', function() {
    // NVDR Excel download
    const nvdrBtn = document.getElementById('nvdr-btn');
    nvdrBtn.addEventListener('click', () => {
        const url = nvdrBtn.getAttribute('data-endpoint');
        withStatus(nvdrBtn, downloadFrom(url));
    });
    
    // Short Sales Excel download
    const shortSalesBtn = document.getElementById('short-sales-btn');
    shortSalesBtn.addEventListener('click', () => {
        const url = shortSalesBtn.getAttribute('data-endpoint');
        withStatus(shortSalesBtn, downloadFrom(url));
    });
    
    // Investor Table CSV download
    const investorTableBtn = document.getElementById('investor-table-btn');
    investorTableBtn.addEventListener('click', () => {
        const market = document.getElementById('market-select').value;
        const url = buildUrl(investorTableBtn.getAttribute('data-endpoint'), { market });
        withStatus(investorTableBtn, downloadFrom(url));
    });
    
    // Investor Chart JSON download
    const investorChartBtn = document.getElementById('investor-chart-btn');
    investorChartBtn.addEventListener('click', () => {
        const market = document.getElementById('market-select').value;
        const url = buildUrl(investorChartBtn.getAttribute('data-endpoint'), { market });
        withStatus(investorChartBtn, downloadFrom(url));
    });
    
    // Sector Constituents CSV download
    const sectorConstituentsBtn = document.getElementById('sector-constituents-btn');
    sectorConstituentsBtn.addEventListener('click', () => {
        const slug = document.getElementById('sector-select').value;
        const url = buildUrl(sectorConstituentsBtn.getAttribute('data-endpoint'), { slug });
        withStatus(sectorConstituentsBtn, downloadFrom(url));
    });
    
    // Save to Database
    const saveDatabaseBtn = document.getElementById('save-database-btn');
    saveDatabaseBtn.addEventListener('click', () => {
        const url = saveDatabaseBtn.getAttribute('data-endpoint');
        withStatus(saveDatabaseBtn, saveToDatabase(url));
    });
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + 1-4 for quick access
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case '1':
                    e.preventDefault();
                    nvdrBtn.click();
                    break;
                case '2':
                    e.preventDefault();
                    shortSalesBtn.click();
                    break;
                case '3':
                    e.preventDefault();
                    investorTableBtn.click();
                    break;
                case '4':
                    e.preventDefault();
                    sectorConstituentsBtn.click();
                    break;
            }
        }
    });
    
    // Add focus management for accessibility
    const focusableElements = document.querySelectorAll('button, select');
    focusableElements.forEach(element => {
        element.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                if (this.tagName === 'BUTTON') {
                    this.click();
                }
            }
        });
    });
    
    // Show welcome message
    console.log('SET Data Export Panel loaded successfully!');
    console.log('Keyboard shortcuts: Ctrl/Cmd + 1-4 for quick access');
});
