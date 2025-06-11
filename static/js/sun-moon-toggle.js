/**
 * Sun/Moon Theme Toggle JavaScript for WallpaperHub
 * Handles the theme switching functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all theme toggle checkboxes
    const themeToggles = document.querySelectorAll('.switch .input');

    // Check for saved theme preference or use device preference
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    const savedTheme = localStorage.getItem('theme');

    // Apply the saved theme or device preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.body.classList.add('dark-theme');
        // Set all checkboxes to checked for dark theme
        themeToggles.forEach(toggle => {
            toggle.checked = true;
        });
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        document.body.classList.remove('dark-theme');
        // Set all checkboxes to unchecked for light theme
        themeToggles.forEach(toggle => {
            toggle.checked = false;
        });
    }

    // Function to toggle theme
    const toggleTheme = (checkbox) => {
        const newTheme = checkbox.checked ? 'dark' : 'light';

        // Apply the new theme
        document.documentElement.setAttribute('data-theme', newTheme);

        // Also add/remove class for compatibility with some templates
        if (newTheme === 'dark') {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }

        // Save the theme preference
        localStorage.setItem('theme', newTheme);

        // Sync all other checkboxes
        themeToggles.forEach(toggle => {
            if (toggle !== checkbox) {
                toggle.checked = checkbox.checked;
            }
        });

        // Force refresh of styles by triggering a reflow
        void document.documentElement.offsetHeight;
    };

    // Add change event listener to all theme toggles
    themeToggles.forEach(toggle => {
        toggle.addEventListener('change', function(e) {
            toggleTheme(this);
            // Prevent event from bubbling up (important for mobile menu)
            e.stopPropagation();
        });

        // Also add click event for better mobile support
        toggle.addEventListener('click', function(e) {
            // Prevent event from bubbling up
            e.stopPropagation();
        });
    });

    // Listen for changes in device theme preference
    prefersDarkScheme.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);

            if (newTheme === 'dark') {
                document.body.classList.add('dark-theme');
            } else {
                document.body.classList.remove('dark-theme');
            }

            // Update all checkboxes
            themeToggles.forEach(toggle => {
                toggle.checked = e.matches;
            });
        }
    });
});
