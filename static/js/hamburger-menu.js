/**
 * Hamburger Menu Functionality for WallpaperHub
 * Provides responsive navigation for mobile devices
 */

document.addEventListener('DOMContentLoaded', function() {
    // Hamburger menu functionality
    const hamburger = document.getElementById('hamburger');
    const mobileNav = document.getElementById('mobileNav');
    const navOverlay = document.getElementById('navOverlay');

    function toggleMobileNav() {
        if (hamburger && mobileNav && navOverlay) {
            hamburger.classList.toggle('active');
            mobileNav.classList.toggle('active');
            navOverlay.classList.toggle('active');
            document.body.style.overflow = mobileNav.classList.contains('active') ? 'hidden' : '';
        }
    }

    function closeMobileNav() {
        if (hamburger && mobileNav && navOverlay) {
            hamburger.classList.remove('active');
            mobileNav.classList.remove('active');
            navOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    // Event listeners
    if (hamburger) {
        hamburger.addEventListener('click', toggleMobileNav);
    }
    
    if (navOverlay) {
        navOverlay.addEventListener('click', closeMobileNav);
    }

    // Close mobile nav when clicking on nav items
    const mobileNavItems = document.querySelectorAll('.mobile-nav-item');
    mobileNavItems.forEach(item => {
        item.addEventListener('click', closeMobileNav);
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeMobileNav();
        }
    });

    // Sync theme toggles between desktop and mobile
    const desktopThemeToggle = document.querySelector('#profile-theme-toggle, #theme-toggle input, .theme-toggle input');
    const mobileThemeToggle = document.getElementById('mobile-theme-toggle');

    if (desktopThemeToggle && mobileThemeToggle) {
        desktopThemeToggle.addEventListener('change', function() {
            mobileThemeToggle.checked = this.checked;
        });

        mobileThemeToggle.addEventListener('change', function() {
            desktopThemeToggle.checked = this.checked;
            // Trigger the theme change event
            desktopThemeToggle.dispatchEvent(new Event('change'));
        });
    }

    // Handle escape key to close mobile nav
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && mobileNav && mobileNav.classList.contains('active')) {
            closeMobileNav();
        }
    });

    // Prevent body scroll when mobile nav is open
    function preventBodyScroll(e) {
        if (mobileNav && mobileNav.classList.contains('active')) {
            e.preventDefault();
        }
    }

    // Add touch event listeners for better mobile experience
    document.addEventListener('touchmove', preventBodyScroll, { passive: false });
});
