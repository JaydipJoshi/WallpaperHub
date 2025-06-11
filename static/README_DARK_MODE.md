# Dark Mode Implementation Guide

This guide explains how to implement the dark mode toggle feature on all pages of the WallpaperHub website.

## Files Created

1. `static/css/theme-styles.css` - Contains all the CSS variables and styles for both light and dark themes
2. `static/js/theme-toggle.js` - JavaScript to handle theme switching and persistence
3. `static/js/theme-init.js` - Script to apply the saved theme before page rendering
4. `Template/theme_includes.html` - HTML snippet with all necessary theme components

## How to Implement on a Page

### 1. Add the data-theme attribute to the HTML tag

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
```

### 2. Include the theme CSS and initialization script in the head

```html
{% load static %}
<!-- In the head section -->
<link rel="stylesheet" href="{% static 'css/theme-styles.css' %}">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
<script src="{% static 'js/theme-init.js' %}"></script>
```

### 3. Update the body and background styles

```css
body {
    background-color: var(--bg-color);
    color: var(--text-color);
    transition: background-color 0.3s ease, color 0.3s ease;
}
```

### 4. Add the theme toggle button to your navigation

```html
<button id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode">
    <i class="bi bi-sun-fill sun-icon"></i>
    <i class="bi bi-moon-fill moon-icon"></i>
</button>
```

### 5. Include the theme toggle script at the end of the body

```html
<!-- At the end of the body -->
<script src="{% static 'js/theme-toggle.js' %}"></script>
```

## CSS Variables Available

The following CSS variables are available for use in your styles:

### Light Theme (Default)
```css
--bg-color: #FFFFFF;
--text-color: #333333;
--card-bg: #FFFFFF;
--card-shadow: rgba(0, 0, 0, 0.1);
--navbar-bg: rgba(255, 255, 255, 0.95);
--border-color: #e0e0e0;
--hero-overlay: rgba(0, 0, 0, 0.7);
--footer-bg: #edf2f7;
--footer-text: #718096;
```

### Dark Theme (Navy Blue)
```css
--bg-color: #0E121B;
--text-color: #E0E0E0;
--card-bg: #161B27;
--card-shadow: rgba(0, 0, 0, 0.4);
--navbar-bg: rgba(14, 18, 27, 0.95);
--border-color: #1E2433;
--hero-overlay: rgba(14, 18, 27, 0.8);
--footer-bg: #0A0E16;
--footer-text: #A0AEC0;
```

## How It Works

1. The theme preference is stored in localStorage
2. The theme is applied on page load before rendering
3. The toggle button switches between light and dark themes
4. The theme is consistent across all pages of the website
5. The system respects the user's device preference if no theme is explicitly set

## Troubleshooting

If the dark mode is not working correctly:

1. Make sure all required files are included
2. Check that the HTML tag has the data-theme attribute
3. Verify that elements are using the CSS variables
4. Ensure the toggle button has the correct ID (theme-toggle)
5. Check the browser console for any JavaScript errors
