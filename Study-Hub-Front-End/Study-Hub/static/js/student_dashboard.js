document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    const token = localStorage.getItem('studentToken');
    const username = localStorage.getItem('studentUsername');
    
    if (!token || !username) {
        window.location.href = '/';
        return;
    }

    // Display username in the dashboard
    document.getElementById('username').textContent = `Welcome, ${username}`;
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

function logout() {
    localStorage.removeItem('studentToken');
    localStorage.removeItem('studentUsername');
    window.location.href = '/';
} 