/**
 * Keyboard shortcut for search functionality in WallpaperHub
 * Implements Ctrl+J shortcut for automatic search focus, similar to Spotify
 */

document.addEventListener('DOMContentLoaded', function() {
    // Function to check if we're on desktop
    function isDesktop() {
        return window.innerWidth >= 768; // Common breakpoint for desktop
    }

    // Detect if user is on Mac
    const isMac = navigator.userAgent.indexOf('Mac') !== -1;

    // Set the appropriate key combination text
    const shortcutKey = isMac ? '⌘+J' : 'Ctrl+J';

    // Function to focus the search input and show visual feedback
    function focusSearchInput() {
        const searchInput = document.getElementById('search-input');

        if (searchInput) {
            // Focus the search input
            searchInput.focus();

            // Add a temporary highlight effect
            searchInput.classList.add('search-shortcut-highlight');

            // Remove the highlight effect after animation completes
            setTimeout(() => {
                searchInput.classList.remove('search-shortcut-highlight');
            }, 1000);

            // Show a toast notification for first-time users
            const hasSeenToast = localStorage.getItem('search-shortcut-toast-shown');

            if (!hasSeenToast) {
                showSearchShortcutToast(shortcutKey);
                localStorage.setItem('search-shortcut-toast-shown', 'true');
            }
        }
    }

    // Function to show a toast notification about the shortcut
    function showSearchShortcutToast() {
        // Check if toast container exists, create if not
        let toastContainer = document.getElementById('toast-container');

        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'toast-notification info';

        // Toast content
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">
                    <i class="bi bi-info-circle"></i>
                </div>
                <div class="toast-message">
                    <strong>Pro Tip:</strong> Press Ctrl+J anytime to quickly search for wallpapers!
                </div>
                <button class="toast-close">&times;</button>
            </div>
            <div class="toast-progress"></div>
        `;

        // Add to container
        toastContainer.appendChild(toast);

        // Add close functionality
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', function() {
            removeToast(toast);
        });

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                removeToast(toast);
            }
        }, 5000);
    }

    // Function to remove a toast with animation
    function removeToast(toast) {
        toast.style.animation = 'slideOut 0.5s ease forwards';
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();

                // If no more toasts, remove the container
                const toastContainer = document.getElementById('toast-container');
                if (toastContainer && toastContainer.children.length === 0) {
                    toastContainer.remove();
                }
            }
        }, 500);
    }

    // Add global keyboard event listener
    document.addEventListener('keydown', function(event) {
        // Check for the appropriate key combination based on platform
        const isMacShortcut = isMac && event.metaKey && event.key.toLowerCase() === 'j';
        const isWinShortcut = !isMac && event.ctrlKey && event.key.toLowerCase() === 'j';

        // If the shortcut is pressed and we're on desktop
        if ((isMacShortcut || isWinShortcut) && isDesktop()) {
            event.preventDefault(); // Prevent default browser behavior
            focusSearchInput();
        }
    });

    // Removed the shortcut indicator as requested by the user
    // The keyboard shortcut still works, but the visual indicator is no longer displayed
});
