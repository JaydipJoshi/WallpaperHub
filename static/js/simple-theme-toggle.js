// Simple Theme Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple theme toggle script loaded');
    
    // Find all theme toggle buttons (desktop and mobile)
    const themeToggles = document.querySelectorAll('.theme-toggle');
    
    // Check for saved theme preference or use device preference
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    const savedTheme = localStorage.getItem('theme');
    
    // Apply the saved theme or device preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
    }
    
    // Function to toggle theme with visual feedback
    const toggleTheme = (button) => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        // Add a visual feedback animation
        button.classList.add('theme-toggle-active');
        setTimeout(() => {
            button.classList.remove('theme-toggle-active');
        }, 300);
        
        // Apply the new theme
        document.documentElement.setAttribute('data-theme', newTheme);
        
        // Save the theme preference
        localStorage.setItem('theme', newTheme);
        console.log('Theme switched to:', newTheme);
    };
    
    // Add click event to all theme toggle buttons
    themeToggles.forEach(button => {
        button.addEventListener('click', function(e) {
            toggleTheme(this);
            // Prevent event from bubbling up (important for mobile menu)
            e.stopPropagation();
        });
    });
    
    // Listen for changes in device theme preference
    prefersDarkScheme.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
        }
    });
});
