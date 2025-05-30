document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('instructorLoginForm');
    const errorMessage = document.getElementById('errorMessage');

    // Check if already logged in
    const token = localStorage.getItem('instructorToken');
    if (token) {
        window.location.href = '/instructor/dashboard';
        return;
    }

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/api/instructor/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                // Store the token in localStorage
                localStorage.setItem('instructorToken', data.token);
                // Redirect to instructor dashboard
                window.location.href = '/instructor/dashboard';
            } else {
                errorMessage.textContent = data.message || 'Login failed';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            console.error('Error:', error);
            errorMessage.textContent = 'An error occurred during login';
            errorMessage.style.display = 'block';
        }
    });
}); 