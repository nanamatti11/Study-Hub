document.addEventListener('DOMContentLoaded', function() {
    // The username is already passed from the server-side template
    // No need for additional API call since server already authenticated
    const usernameElement = document.getElementById('username');
    if (usernameElement) {
        // The username is already set by the template, just ensure it's visible
        console.log('Student dashboard loaded successfully');
    } else {
        console.error('Username element not found');
    }
});

function navigateToSection(section) {
    // Add fade-out animation to all buttons
    const buttons = document.querySelectorAll('.dashboard-btn');
    buttons.forEach(button => {
        button.classList.add('fade-out');
    });

    // Navigate after animation
    setTimeout(() => {
        window.location.href = `/student/${section}`;
    }, 500);
}

function backToDashboard() {
    window.location.href = '/student/dashboard';
}

function toggleProfileDropdown() {
    const dropdown = document.getElementById('profileDropdown');
    dropdown.classList.toggle('show');
}

function viewProfile() {
    // Close dropdown
    document.getElementById('profileDropdown').classList.remove('show');
    // Placeholder for profile functionality
    alert('Profile feature coming soon!');
}

function logout() {
    // Close dropdown
    document.getElementById('profileDropdown').classList.remove('show');
    
    // Clear localStorage items
    localStorage.removeItem('studentToken');
    localStorage.removeItem('studentUsername');
    
    // Clear the cookie by making a request to logout endpoint
    fetch('/api/student/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(() => {
        window.location.href = '/';
    })
    .catch(() => {
        window.location.href = '/';
    });
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const profileContainer = document.querySelector('.profile-container');
    const dropdown = document.getElementById('profileDropdown');
    
    if (!profileContainer.contains(event.target)) {
        dropdown.classList.remove('show');
    }
}); 