// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Find the Explore More button
    const loadMoreBtn = document.getElementById('load-more-btn');
    
    if (loadMoreBtn) {
        console.log('Found Explore More button');
        
        // Add click event listener
        loadMoreBtn.addEventListener('click', function() {
            // Get page and query from button attributes
            const page = this.getAttribute('data-page');
            const query = this.getAttribute('data-query');
            
            console.log('Loading more images for query:', query, 'page:', page);
            
            // Disable button while loading
            this.disabled = true;
            this.textContent = 'Loading...';
            
            // Make AJAX request
            fetch(`?query=${encodeURIComponent(query)}&page=${page}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data);
                
                // Process the response
                if (data.images && data.images.length > 0) {
                    // Get the results container
                    const resultsContainer = document.getElementById('search-results');
                    
                    if (!resultsContainer) {
                        throw new Error('Results container not found');
                    }
                    
                    // Add each new image
                    data.images.forEach(image => {
                        // Create wallpaper item
                        const wallpaperItem = document.createElement('div');
                        wallpaperItem.className = 'wallpaper-item';
                        
                        // Create link
                        const link = document.createElement('a');
                        link.href = `/wallpaper/${image.id}/`;
                        link.className = 'wallpaper-link';
                        
                        // Create image wrapper
                        const imgWrapper = document.createElement('div');
                        imgWrapper.className = 'img-loading-wrapper';
                        
                        // Create loading placeholder
                        const loadingPlaceholder = document.createElement('div');
                        loadingPlaceholder.className = 'loading-placeholder';
                        imgWrapper.appendChild(loadingPlaceholder);
                        
                        // Create image
                        const img = document.createElement('img');
                        img.src = image.urls.small;
                        img.alt = image.alt_description || 'Wallpaper';
                        img.loading = 'lazy';
                        
                        // Handle image load events
                        img.onload = function() {
                            loadingPlaceholder.style.opacity = '0';
                        };
                        
                        img.onerror = function() {
                            this.src = 'https://via.placeholder.com/400x600?text=Image+Not+Available';
                            loadingPlaceholder.style.display = 'none';
                        };
                        
                        imgWrapper.appendChild(img);
                        
                        // Create overlay
                        const overlay = document.createElement('div');
                        overlay.className = 'overlay';
                        
                        // Create title
                        const title = document.createElement('h3');
                        title.textContent = image.alt_description || 'Beautiful Wallpaper';
                        overlay.appendChild(title);
                        
                        // Assemble elements
                        link.appendChild(imgWrapper);
                        link.appendChild(overlay);
                        wallpaperItem.appendChild(link);
                        resultsContainer.appendChild(wallpaperItem);
                    });
                    
                    // Update button or remove it
                    if (data.has_more) {
                        this.setAttribute('data-page', parseInt(page) + 1);
                        this.disabled = false;
                        this.textContent = 'Explore More';
                    } else {
                        this.parentNode.removeChild(this);
                        alert("You've reached the end of the results");
                    }
                    
                    // Show success message
                    alert(`Loaded ${data.images.length} more wallpapers`);
                } else {
                    // No images found
                    this.disabled = false;
                    this.textContent = 'No More Results';
                    setTimeout(() => {
                        this.parentNode.removeChild(this);
                    }, 2000);
                }
            })
            .catch(error => {
                console.error('Error loading more images:', error);
                this.disabled = false;
                this.textContent = 'Try Again';
                alert('Error loading more images. Please try again.');
            });
        });
    } else {
        console.warn('Explore More button not found');
    }
});
