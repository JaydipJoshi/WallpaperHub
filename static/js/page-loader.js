/**
 * Page Loader Script for WallpaperHub
 * Displays a loading animation until the page is fully loaded
 * Then smoothly fades out the loader
 */

// Create and insert the loader HTML as soon as the script runs
(function() {
  // Create loader container
  const loaderContainer = document.createElement('div');
  loaderContainer.className = 'loader-container';

  // Create Easter egg animation HTML
  loaderContainer.innerHTML = `
    <div class="easter-animation">
      <div class="egg">
        <div class="eyes"></div>
      </div>
      <div class="shadow"></div>
      <div class="clouds">
        <div class="cloud1"></div>
        <div class="cloud2"></div>
        <div class="cloud3"></div>
      </div>
    </div>
  `;

  // Add to document as first child of body
  document.body.insertBefore(loaderContainer, document.body.firstChild);
})();

// Hide loader when page is fully loaded
window.addEventListener('load', function() {
  // Get the loader container
  const loaderContainer = document.querySelector('.loader-container');

  // Add hidden class to fade it out
  if (loaderContainer) {
    loaderContainer.classList.add('hidden');

    // Remove from DOM after animation completes
    setTimeout(function() {
      if (loaderContainer.parentNode) {
        loaderContainer.parentNode.removeChild(loaderContainer);
      }
    }, 500); // Match this to the CSS transition duration
  }
});

// Performance optimizations
document.addEventListener('DOMContentLoaded', function() {
  // Lazy load images that are not in the viewport
  if ('loading' in HTMLImageElement.prototype) {
    // Browser supports native lazy loading
    const images = document.querySelectorAll('img:not([loading])');
    images.forEach(img => {
      if (!img.hasAttribute('loading') && !img.classList.contains('no-lazy')) {
        img.setAttribute('loading', 'lazy');
      }
    });
  } else {
    // Fallback for browsers that don't support lazy loading
    // You could add a lazy loading library here if needed
  }

  // Defer non-critical JavaScript
  const deferScripts = document.querySelectorAll('script[data-defer]');
  deferScripts.forEach(script => {
    const newScript = document.createElement('script');

    // Copy all attributes
    Array.from(script.attributes).forEach(attr => {
      if (attr.name !== 'data-defer') {
        newScript.setAttribute(attr.name, attr.value);
      }
    });

    // Set content if it's an inline script
    if (script.innerHTML) {
      newScript.innerHTML = script.innerHTML;
    }

    // Replace the original script
    script.parentNode.replaceChild(newScript, script);
  });
});
