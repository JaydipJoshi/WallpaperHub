# Responsive Theme Toggle Implementation Guide

This guide explains how to implement the dark mode toggle feature on all pages of the WallpaperHub website, ensuring it works well on both desktop and mobile devices.

## Implementation Overview

The theme toggle functionality is implemented in two places:
1. In the desktop navigation menu
2. In the mobile dropdown menu

## Files Used

1. `static/css/theme-styles.css` - Contains all the CSS variables and styles for both light and dark themes
2. `static/js/theme-toggle.js` - JavaScript to handle theme switching and persistence
3. `static/js/theme-init.js` - Script to apply the saved theme before page rendering

## Desktop Implementation

Add the theme toggle button to your desktop navigation:

```html
<button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">
    <i class="bi bi-sun-fill sun-icon"></i>
    <i class="bi bi-moon-fill moon-icon"></i>
</button>
```

## Mobile Implementation

Add the theme toggle button to your mobile dropdown menu:

```html
<div class="dropdown-item theme-toggle-container">
    <span>Theme:</span>
    <button id="mobile-theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">
        <i class="bi bi-sun-fill sun-icon"></i>
        <i class="bi bi-moon-fill moon-icon"></i>
    </button>
</div>
```

## CSS Styles

The theme toggle buttons use these CSS classes:

1. `.theme-toggle` - The main button style
2. `.theme-toggle-container` - Container for the mobile toggle with label
3. `.sun-icon` and `.moon-icon` - The icons that animate during toggle

## JavaScript Implementation

The theme-toggle.js script handles both toggle buttons:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const mobileThemeToggle = document.getElementById('mobile-theme-toggle');
    
    // Function to toggle theme
    const toggleTheme = () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        // Apply the new theme
        document.documentElement.setAttribute('data-theme', newTheme);
        
        // Save the theme preference
        localStorage.setItem('theme', newTheme);
    };
    
    // Toggle theme when desktop button is clicked
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Toggle theme when mobile button is clicked
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', function(e) {
            // Prevent the dropdown from closing
            e.stopPropagation();
            toggleTheme();
        });
    }
});
```

## Dark Mode Styles for Dropdowns

Add these styles to ensure dropdowns look good in dark mode:

```css
[data-theme="dark"] .dropdown-item:hover {
    background-color: #1E2433;
    color: #6D9CFF;
}

[data-theme="dark"] .mobile-dropdown,
[data-theme="dark"] .user-dropdown {
    background-color: var(--card-bg);
    box-shadow: 0 5px 15px var(--card-shadow);
}

[data-theme="dark"] .dropdown-header,
[data-theme="dark"] .dropdown-item {
    color: var(--text-color);
}

[data-theme="dark"] .dropdown-divider {
    border-color: var(--border-color);
}
```

## Troubleshooting

If the sun icon is not visible in dark mode:
- Make sure the icon has a contrasting color in dark mode
- Check that the z-index is appropriate
- Verify that the opacity and transform properties are working correctly
