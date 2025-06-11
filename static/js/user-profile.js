/**
 * User Profile Dropdown Functionality for WallpaperHub
 */

document.addEventListener('DOMContentLoaded', function() {
  // Find all user profile elements
  const userProfiles = document.querySelectorAll('.user-profile');

  userProfiles.forEach(profile => {
    // Add click event to toggle dropdown
    profile.addEventListener('click', function(e) {
      e.stopPropagation(); // Prevent event bubbling

      // Close all other dropdowns first
      userProfiles.forEach(otherProfile => {
        if (otherProfile !== this) {
          const otherDropdown = otherProfile.querySelector('.user-dropdown');
          if (otherDropdown && otherDropdown.classList.contains('active')) {
            otherDropdown.classList.remove('active');
          }
        }
      });

      // Toggle active class on dropdown
      const dropdown = this.querySelector('.user-dropdown');
      if (dropdown) {
        dropdown.classList.toggle('active');
      }
    });
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function(e) {
    userProfiles.forEach(profile => {
      const dropdown = profile.querySelector('.user-dropdown');
      if (dropdown && dropdown.classList.contains('active')) {
        dropdown.classList.remove('active');
      }
    });
  });
});
