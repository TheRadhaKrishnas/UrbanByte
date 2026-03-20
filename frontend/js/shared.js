/**
 * shared.js – Common functionality for all dashboard pages
 * This file should be included on every dashboard page (member-dashboard.html, management-dashboard.html, and all subpages)
 * It depends on functions from auth.js (checkAuth, logout)
 */

// ==================== LOAD USER INFO INTO SIDEBAR ====================
function loadUserSidebar() {
  const userJson = sessionStorage.getItem('user');
  if (!userJson) return; // should not happen if checkAuth passed, but just in case

  const user = JSON.parse(userJson);
  
  // Update user icon (initials)
  const userIcon = document.getElementById('userIcon');
  if (userIcon) {
    userIcon.textContent = user.name ? user.name.charAt(0).toUpperCase() : 'U';
  }

  // Update user name display
  const userName = document.getElementById('userName');
  if (userName) {
    userName.textContent = user.name || 'User';
  }

  // Optionally, update welcome message if present (like on dashboard main)
  const welcomeName = document.getElementById('welcomeName');
  if (welcomeName) {
    welcomeName.textContent = user.name || 'Member';
  }
  const welcomeFlat = document.getElementById('welcomeFlat');
  if (welcomeFlat && user.flat) {
    welcomeFlat.textContent = user.flat;
  }
  const welcomeDesignation = document.getElementById('welcomeDesignation');
  if (welcomeDesignation && user.designation) {
    welcomeDesignation.textContent = user.designation;
  }
}

// ==================== ATTACH LOGOUT BUTTON ====================
function attachLogout() {
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function(e) {
      e.preventDefault();
      logout(); // from auth.js
    });
  }
}

// ==================== DASHBOARD INIT ====================
// This runs on any page with class "dashboard"
document.addEventListener('DOMContentLoaded', function() {
  if (document.querySelector('.dashboard')) {
    // First, check authentication (redirects if not logged in or wrong role)
    // Adjust allowed roles based on page? We can detect from URL or a data attribute.
    // For simplicity, we'll check the current page filename.
    const path = window.location.pathname.split('/').pop();
    let allowed = ['member', 'management']; // default allow both

    if (path.startsWith('member-') || path === 'profile.html' || path === 'complaint.html' || path === 'polls-forum.html' || path === 'emergency-contact.html' || path === 'payment.html' || path === 'documents.html') {
      // These pages are accessible by members (and possibly management too, but management has own versions)
      // We'll keep both allowed for now.
    } else if (path.startsWith('management-') || path === 'member-database.html' || path === 'contract-details.html') {
      allowed = ['management']; // management only
    }

    const user = checkAuth(allowed); // defined in auth.js
    if (user) {
      loadUserSidebar();
      attachLogout();
    }
  }
});