// Global state
let currentPage = 'inventory';
let isAuthenticated = false;

// Load components
async function loadComponent(elementId, componentPath) {
    try {
        const response = await fetch(componentPath);
        const html = await response.text();
        document.getElementById(elementId).innerHTML = html;
    } catch (error) {
        console.error('Error loading component:', error);
    }
}

// Function to show different pages
async function showPage(pageName) {
    currentPage = pageName;
    await loadComponent('page-container', `pages/${pageName}.html`);
    
    // Update active state in navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.querySelector(`.nav-btn[onclick="showPage('${pageName}')"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Dispatch event for page change
    window.dispatchEvent(new CustomEvent('showPage', { detail: pageName }));
}

// Handle authentication
window.handleAuth = function(action) {
    if (action === 'signin') {
        const storeName = document.getElementById('store-name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        // Simple validation
        if (storeName && email && password) {
            isAuthenticated = true;
            document.getElementById('auth-container').style.display = 'none';
            document.getElementById('app-section').style.display = 'flex';
            showPage('inventory');
        } else {
            alert('Please fill in all fields');
        }
    } else if (action === 'signup') {
        // For demo purposes, just sign in
        handleAuth('signin');
    }
};

// Handle logout
window.logout = function() {
    isAuthenticated = false;
    document.getElementById('auth-container').style.display = 'block';
    document.getElementById('app-section').style.display = 'none';
    loadComponent('auth-container', 'pages/auth.html');
};

// Load initial components
document.addEventListener('DOMContentLoaded', () => {
    loadComponent('auth-container', 'pages/auth.html');
}); 