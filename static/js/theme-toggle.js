// Theme Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const mobileThemeToggle = document.getElementById('mobile-theme-toggle');

    // Check for saved theme preference or use device preference
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    const savedTheme = localStorage.getItem('theme');

    // Apply the saved theme or device preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        // Set checkboxes to checked for dark theme
        if (themeToggle) themeToggle.checked = true;
        if (mobileThemeToggle) mobileThemeToggle.checked = true;
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        // Set checkboxes to unchecked for light theme
        if (themeToggle) themeToggle.checked = false;
        if (mobileThemeToggle) mobileThemeToggle.checked = false;
    }

    // Function to toggle theme with visual feedback
    const toggleTheme = (checkbox) => {
        const newTheme = checkbox.checked ? 'dark' : 'light';

        // Add a visual feedback animation to the parent label
        const label = checkbox.closest('.switch');
        if (label) {
            label.classList.add('theme-toggle-active');
            setTimeout(() => {
                label.classList.remove('theme-toggle-active');
            }, 300);
        }

        // Apply the new theme
        document.documentElement.setAttribute('data-theme', newTheme);

        // Save the theme preference
        localStorage.setItem('theme', newTheme);

        // Sync the other checkbox
        if (checkbox === themeToggle && mobileThemeToggle) {
            mobileThemeToggle.checked = checkbox.checked;
        } else if (checkbox === mobileThemeToggle && themeToggle) {
            themeToggle.checked = checkbox.checked;
        }
    };

    // Toggle theme when desktop checkbox is changed
    if (themeToggle) {
        themeToggle.addEventListener('change', function() {
            toggleTheme(this);
        });
    }

    // Toggle theme when mobile checkbox is changed
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('change', function(e) {
            // Prevent the dropdown from closing
            e.stopPropagation();
            toggleTheme(this);
        });
    }

    // Listen for changes in device theme preference
    prefersDarkScheme.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
        }
    });
});
