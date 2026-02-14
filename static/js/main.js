// Main JavaScript for AI Code Reviewer - SIMPLIFIED (No WebSocket)

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeCharts();
    loadUserHistory();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        try {
            new bootstrap.Tooltip(tooltip);
        } catch (e) {}
    });
}

// Initialize charts on dashboard
function initializeCharts() {
    if (document.getElementById('radarChart')) {
        loadDashboardData();
    }
}

// Load user history for dashboard
async function loadUserHistory() {
    try {
        const response = await fetch('/api/user/history');
        const data = await response.json();
        
        if (data.reviews) {
            displayRecentReviews(data.reviews);
        }
    } catch (error) {
        console.error('Error loading user history:', error);
    }
}

// Display recent reviews in dashboard
function displayRecentReviews(reviews) {
    const container = document.getElementById('recent-reviews');
    if (!container) return;
    
    container.innerHTML = '';
    
    reviews.slice(0, 5).forEach(review => {
        const row = document.createElement('tr');
        row.className = 'border-b hover:bg-gray-50';
        row.innerHTML = `
            <td class="py-2">${review.project || 'Code Snippet'}</td>
            <td class="py-2">${new Date(review.timestamp).toLocaleDateString()}</td>
            <td class="py-2">
                <span class="px-2 py-1 rounded ${getScoreColorClass(review.overall_score)}">
                    ${review.overall_score || 0}%
                </span>
            </td>
            <td class="py-2">
                <span class="px-2 py-1 rounded bg-green-100 text-green-800">
                    completed
                </span>
            </td>
            <td class="py-2">
                <button onclick="viewReview('${review.review_id}')" class="text-indigo-600 hover:text-indigo-800">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        container.appendChild(row);
    });
}

// Helper function for score color
function getScoreColorClass(score) {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
}

// View specific review
function viewReview(reviewId) {
    window.location.href = `/review/result/${reviewId}`;
}

// Submit code for review
async function submitCode() {
    const editor = document.querySelector('.CodeMirror')?.CodeMirror;
    if (!editor) {
        alert('Editor not initialized');
        return;
    }
    
    const code = editor.getValue();
    if (!code.trim()) {
        alert('Please paste some code to review');
        return;
    }
    
    // Show loading
    const loadingModal = document.getElementById('loading-modal');
    if (loadingModal) {
        loadingModal.classList.remove('hidden');
        loadingModal.classList.add('flex');
    }
    
    // Prepare data
    const data = {
        code: code,
        language: document.getElementById('language')?.value || 'python',
        plagiarism_check: document.getElementById('plagiarism-check')?.checked || false,
        deep_analysis: document.getElementById('deep-analysis')?.checked || false
    };
    
    try {
        const response = await fetch('/api/review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = `/review/result/${result.review_id}`;
        } else {
            alert('Error: ' + result.error);
            if (loadingModal) {
                loadingModal.classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during review');
        if (loadingModal) {
            loadingModal.classList.add('hidden');
        }
    }
}

// Analyze GitHub repository
// Analyze GitHub repository - FIXED VERSION (no Swal dependency)
async function analyzeRepo() {
    const url = document.getElementById('repo-url')?.value;
    if (!url) {
        alert('Please enter a GitHub repository URL');
        return;
    }
    
    // Show simple loading alert instead of Swal
    alert('Analyzing repository... Please wait.');
    
    try {
        const response = await fetch('/api/analyze-repo', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repo_url: url,
                branch: document.getElementById('branch')?.value || 'main',
                options: {
                    include_tests: document.getElementById('include-tests')?.checked || true,
                    deep_scan: document.getElementById('deep-scan')?.checked || true,
                    dependency_check: document.getElementById('dependency-check')?.checked || true,
                    plagiarism_check: document.getElementById('plagiarism-repo')?.checked || true
                }
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = `/review/result/${result.review_id}`;
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to analyze repository: ' + error.message);
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        'bg-blue-500'
    }`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    showToast('Copied to clipboard!', 'success');
}

// Tab switching for results page
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(`tab-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }
    
    // Update button styles
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('border-indigo-500', 'text-indigo-600');
        button.classList.add('border-transparent', 'text-gray-500');
    });
    
    const activeButton = event?.target;
    if (activeButton) {
        activeButton.classList.add('border-indigo-500', 'text-indigo-600');
        activeButton.classList.remove('border-transparent', 'text-gray-500');
    }
}

// Export report
async function exportReport(reviewId) {
    window.location.href = `/api/export/${reviewId}`;
}

// Share review
function shareReview(reviewId) {
    const url = `${window.location.origin}/review/result/${reviewId}`;
    navigator.clipboard.writeText(url);
    showToast('Link copied to clipboard!', 'success');
}

// Notify for premium
function notifyMe() {
    alert("Thanks! We'll notify you when premium features launch.");
}