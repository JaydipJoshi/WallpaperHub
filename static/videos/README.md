# WallpaperHub Video Assets

## Custom Promotional Video

To add your custom WallpaperHub promotional video:

1. **Video Requirements:**
   - Format: MP4 (recommended)
   - Resolution: 1920x1080 (Full HD) or higher
   - Duration: 30-60 seconds (recommended)
   - File size: Under 50MB for web optimization

2. **Add Your Video:**
   - Place your video file in this directory: `static/videos/`
   - Recommended filename: `wallpaperhub-promo.mp4`

3. **Update the Landing Page:**
   - Open `Template/landingPage.html`
   - Find the video source section (around line 720)
   - Replace the current video URL with your custom video:
   ```html
   <source src="{% static 'videos/wallpaperhub-promo.mp4' %}" type="video/mp4">
   ```

4. **Add a Poster Image (Optional):**
   - Create a poster image (1920x1080 recommended)
   - Place it in `static/images/`
   - Update the poster attribute:
   ```html
   poster="{% static 'images/video-poster.jpg' %}"
   ```

## Video Content Suggestions

Based on your prompt, your video should include:

- **3D delivery-style character** wearing a yellow hoodie and cap
- **Smartphone showcase** with beautiful, colorful wallpapers
- **Character gestures** toward the phone as wallpapers scroll
- **Text overlays:** "Explore Wallpapers", "Save & Share", "Get Started"
- **WallpaperHub branding** (ensure correct spelling)
- **Logo animation** at the end
- **Glowing call-to-action button**
- **Bright colors** and smooth transitions
- **Techy, fun atmosphere**

## Current Fallback

The landing page currently uses a sample video from Google's test videos. This will be replaced automatically when you add your custom video using the instructions above.

## Technical Notes

- The video player supports autoplay on user interaction
- Includes accessibility features (keyboard navigation)
- Responsive design for mobile devices
- Fallback content for browsers that don't support video
- Loading states and error handling included
