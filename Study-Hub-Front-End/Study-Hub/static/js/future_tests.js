document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    const token = localStorage.getItem('studentToken');
    if (!token) {
        window.location.href = '/';
        return;
    }

    // Show loading animation
    const loadingAnimation = document.getElementById('loadingAnimation');
    const testsDisplay = document.getElementById('testsDisplay');

    // Simulate loading time (you can replace this with actual API call)
    setTimeout(() => {
        loadingAnimation.style.display = 'none';
        testsDisplay.style.display = 'block';
    }, 1500);

    // Handle back button
    document.querySelector('.btn-back').addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = '/student/dashboard';
    });
});

// Remove or comment out unused functions
// function loadStudentInfo() { ... }
// function loadFutureTests() { ... }
// function displayTests(tests) { ... }
// function backToDashboard() { ... } 