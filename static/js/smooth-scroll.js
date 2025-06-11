/**
 * Smooth Scrolling functionality for WallpaperHub
 * This script provides smooth scrolling behavior for the entire website
 */

document.addEventListener('DOMContentLoaded', function() {
    // Apply smooth scrolling to the entire document
    document.documentElement.style.scrollBehavior = 'smooth';

    // Get all links that navigate to an ID on the same page
    const internalLinks = document.querySelectorAll('a[href^="#"]');

    // Add click event listeners to all internal links
    internalLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Get the target element
            const targetId = this.getAttribute('href');

            // Skip if it's just "#" (often used for buttons)
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);

            // If the target element exists
            if (targetElement) {
                e.preventDefault();

                // Get the navbar height for offset (if navbar exists)
                const navbar = document.querySelector('.navbar');
                const navbarHeight = navbar ? navbar.offsetHeight : 0;

                // Calculate the target position with offset
                const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - navbarHeight - 20;

                // Scroll smoothly to the target
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Smooth scroll to top button functionality
    const scrollTopButton = document.getElementById('scroll-to-top');
    if (scrollTopButton) {
        // Show/hide the button based on scroll position
        function updateScrollButtonVisibility() {
            if (window.pageYOffset > 300) {
                scrollTopButton.classList.add('show');
            } else {
                scrollTopButton.classList.remove('show');
            }
        }

        // Initial check on page load
        updateScrollButtonVisibility();

        // Update on scroll
        window.addEventListener('scroll', updateScrollButtonVisibility);

        // Also update on resize and orientation change for mobile devices
        window.addEventListener('resize', updateScrollButtonVisibility);
        window.addEventListener('orientationchange', updateScrollButtonVisibility);

        // Scroll to top when clicked - add multiple event listeners for mobile
        ['click', 'touchend'].forEach(eventType => {
            scrollTopButton.addEventListener(eventType, function(e) {
                e.preventDefault();
                e.stopPropagation();
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });
        });
    }

    // Add smooth scrolling to navigation menu items
    const navLinks = document.querySelectorAll('.nav-link, .drawer-item');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');

            // Only handle links to IDs on the same page
            if (href && href.startsWith('#') && href !== '#') {
                const targetElement = document.querySelector(href);

                if (targetElement) {
                    e.preventDefault();

                    // Close the mobile menu if it's open
                    const sideDrawer = document.querySelector('.side-drawer');
                    const drawerOverlay = document.querySelector('.drawer-overlay');

                    if (sideDrawer && sideDrawer.classList.contains('active')) {
                        sideDrawer.classList.remove('active');
                        if (drawerOverlay) drawerOverlay.classList.remove('active');
                    }

                    // Get the navbar height for offset
                    const navbar = document.querySelector('.navbar');
                    const navbarHeight = navbar ? navbar.offsetHeight : 0;

                    // Calculate the target position with offset
                    const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - navbarHeight - 20;

                    // Scroll smoothly to the target
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
});

// Add smooth scrolling for "back to top" functionality
function scrollToTop(e) {
    // Prevent default behavior if event is provided
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Force scroll to top with both methods for maximum compatibility
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });

    // Alternative method for older browsers and some mobile devices
    document.body.scrollTop = 0; // For Safari
    document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera

    return false;
}

// Support for custom "Back to top" buttons
document.addEventListener('DOMContentLoaded', function() {
    // Find all elements with class 'back-to-top' or similar classes
    const backToTopButtons = document.querySelectorAll('.back-to-top, .back_to_top, [id*="back-to-top"], [id*="backToTop"]');

    backToTopButtons.forEach(button => {
        // Only add the event listener if it doesn't already have one
        if (!button.hasAttribute('data-smooth-scroll-initialized')) {
            button.setAttribute('data-smooth-scroll-initialized', 'true');
            button.addEventListener('click', function(e) {
                e.preventDefault();
                scrollToTop();
            });
        }
    });
});

// Add smooth scrolling to a specific element
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        // Get the navbar height for offset
        const navbar = document.querySelector('.navbar');
        const navbarHeight = navbar ? navbar.offsetHeight : 0;

        // Calculate the target position with offset
        const targetPosition = element.getBoundingClientRect().top + window.pageYOffset - navbarHeight - 20;

        // Scroll smoothly to the target
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }
}
