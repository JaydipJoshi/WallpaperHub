/**
 * Cookie Consent Script for WallpaperHub
 * Handles displaying and managing cookie consent preferences
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if user has already accepted cookies
    const cookieConsent = localStorage.getItem('cookieConsent');
    
    // If consent hasn't been given, show the banner
    if (!cookieConsent) {
        showCookieConsentBanner();
    }
    
    // Add event listeners to the cookie consent buttons
    setupEventListeners();
});

/**
 * Shows the cookie consent banner
 */
function showCookieConsentBanner() {
    const banner = document.getElementById('cookie-consent-banner');
    if (banner) {
        // Add a small delay for better UX (don't show immediately on page load)
        setTimeout(() => {
            banner.classList.add('active');
        }, 1000);
    }
}

/**
 * Sets up event listeners for the cookie consent buttons
 */
function setupEventListeners() {
    // Accept button
    const acceptButton = document.querySelector('#cookie-consent-banner .accept-button');
    if (acceptButton) {
        acceptButton.addEventListener('click', function() {
            acceptCookies();
        });
    }
    
    // More options button
    const moreOptionsButton = document.querySelector('#cookie-consent-banner .more-options-button');
    if (moreOptionsButton) {
        moreOptionsButton.addEventListener('click', function() {
            showMoreOptions();
        });
    }
}

/**
 * Handles accepting all cookies
 */
function acceptCookies() {
    // Save consent in localStorage
    localStorage.setItem('cookieConsent', 'accepted');
    localStorage.setItem('cookieConsentTimestamp', Date.now());
    
    // Hide the banner with animation
    const banner = document.getElementById('cookie-consent-banner');
    if (banner) {
        banner.classList.remove('active');
        banner.classList.add('hiding');
        
        // Remove from DOM after animation completes
        setTimeout(() => {
            if (banner.parentNode) {
                banner.parentNode.removeChild(banner);
            }
        }, 500); // Match this to the CSS transition duration
    }
}

/**
 * Shows more cookie options (redirects to privacy policy)
 */
function showMoreOptions() {
    // Redirect to privacy policy page
    window.location.href = '/privacyPolicy.html';
}
