// Custom Theme Switch Functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Custom theme switch script loaded');

    // Wait a short time to ensure all elements are loaded
    setTimeout(() => {
        initializeThemeToggle();
    }, 100);
});

// Function to initialize the theme toggle
function initializeThemeToggle() {
    console.log('Initializing theme toggle');
    const themeCheckbox = document.getElementById('theme-checkbox');
    const mobileThemeCheckbox = document.getElementById('mobile-theme-checkbox');

    console.log('Theme checkboxes:', themeCheckbox, mobileThemeCheckbox);

    // Check for saved theme preference or use device preference
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    const savedTheme = localStorage.getItem('theme');
    console.log('Saved theme:', savedTheme);

    // Apply the saved theme or device preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        if (themeCheckbox) themeCheckbox.checked = true;
        if (mobileThemeCheckbox) mobileThemeCheckbox.checked = true;
        console.log('Applied dark theme');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        if (themeCheckbox) themeCheckbox.checked = false;
        if (mobileThemeCheckbox) mobileThemeCheckbox.checked = false;
        console.log('Applied light theme');
    }

    // Function to toggle theme
    const toggleTheme = (checkbox) => {
        console.log('Toggle theme called with checkbox:', checkbox.id, 'checked:', checkbox.checked);
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = checkbox.checked ? 'dark' : 'light';
        console.log('Switching from', currentTheme, 'to', newTheme);

        // Apply the new theme
        document.documentElement.setAttribute('data-theme', newTheme);

        // Save the theme preference
        localStorage.setItem('theme', newTheme);
        console.log('Saved theme preference:', newTheme);

        // Sync the other checkbox
        if (checkbox.id === 'theme-checkbox' && mobileThemeCheckbox) {
            console.log('Syncing mobile checkbox');
            mobileThemeCheckbox.checked = checkbox.checked;
        } else if (checkbox.id === 'mobile-theme-checkbox' && themeCheckbox) {
            console.log('Syncing desktop checkbox');
            themeCheckbox.checked = checkbox.checked;
        }
    };

    // Toggle theme when desktop checkbox is clicked
    if (themeCheckbox) {
        console.log('Adding event listener to desktop checkbox');
        themeCheckbox.addEventListener('change', function() {
            console.log('Desktop checkbox changed');
            toggleTheme(this);
        });
        // Also add click event for better mobile support
        themeCheckbox.addEventListener('click', function(e) {
            console.log('Desktop checkbox clicked');
        });
    }

    // Toggle theme when mobile checkbox is clicked
    if (mobileThemeCheckbox) {
        console.log('Adding event listener to mobile checkbox');

        // Direct click handler for mobile
        const mobileToggleContainer = document.querySelector('.theme-toggle-container');
        if (mobileToggleContainer) {
            mobileToggleContainer.addEventListener('click', function(e) {
                console.log('Mobile toggle container clicked');
                // Prevent event from bubbling up to close the dropdown
                e.stopPropagation();
            });
        }

        // Handle the label click for mobile
        const mobileToggleLabel = mobileThemeCheckbox.closest('.switch');
        if (mobileToggleLabel) {
            mobileToggleLabel.addEventListener('click', function(e) {
                console.log('Mobile toggle label clicked');
                // Toggle the checkbox state manually
                mobileThemeCheckbox.checked = !mobileThemeCheckbox.checked;
                // Call toggle theme with the checkbox
                toggleTheme(mobileThemeCheckbox);
                // Prevent default to avoid double-toggling
                e.preventDefault();
                // Prevent event from bubbling up
                e.stopPropagation();
            });
        }

        // Handle clicks on the slider and its elements
        const mobileSlider = mobileToggleLabel ? mobileToggleLabel.querySelector('.slider') : null;
        if (mobileSlider) {
            mobileSlider.addEventListener('click', function(e) {
                console.log('Mobile slider clicked');
                // Toggle the checkbox state manually
                mobileThemeCheckbox.checked = !mobileThemeCheckbox.checked;
                // Call toggle theme with the checkbox
                toggleTheme(mobileThemeCheckbox);
                // Prevent default to avoid double-toggling
                e.preventDefault();
                // Prevent event from bubbling up
                e.stopPropagation();
            });

            // Also handle clicks on stars and cloud
            const sliderElements = mobileSlider.querySelectorAll('.star, .cloud');
            sliderElements.forEach(element => {
                element.addEventListener('click', function(e) {
                    console.log('Mobile slider element clicked');
                    // Toggle the checkbox state manually
                    mobileThemeCheckbox.checked = !mobileThemeCheckbox.checked;
                    // Call toggle theme with the checkbox
                    toggleTheme(mobileThemeCheckbox);
                    // Prevent default to avoid double-toggling
                    e.preventDefault();
                    // Prevent event from bubbling up
                    e.stopPropagation();
                });
            });
        }

        // Standard change event
        mobileThemeCheckbox.addEventListener('change', function() {
            console.log('Mobile checkbox changed');
            toggleTheme(this);
        });

        // Direct click on checkbox
        mobileThemeCheckbox.addEventListener('click', function(e) {
            console.log('Mobile checkbox clicked');
            // Prevent event from bubbling up
            e.stopPropagation();
        });
    }

    // Listen for changes in device theme preference
    prefersDarkScheme.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            if (themeCheckbox) themeCheckbox.checked = e.matches;
            if (mobileThemeCheckbox) mobileThemeCheckbox.checked = e.matches;
        }
    });

    // Add a global click handler to ensure the mobile menu stays open when clicking the theme toggle
    document.addEventListener('click', function(e) {
        // Check if the click is on or within the mobile theme toggle
        if (e.target && (e.target.id === 'mobile-theme-checkbox' ||
            (e.target.closest('.switch') && e.target.closest('.theme-toggle-container')))) {
            console.log('Preventing mobile menu close from global handler');
            e.stopPropagation();
        }
    }, true);
});
