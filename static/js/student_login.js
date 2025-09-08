document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form values
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/api/student/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ username, password }),
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                // Store token in localStorage
                localStorage.setItem('studentToken', data.token);
                localStorage.setItem('studentUsername', username);
                
                // Redirect to dashboard
                window.location.href = '/student/dashboard';
            } else {
                errorMessage.textContent = data.message || 'Login failed. Please try again.';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            console.error('Login error:', error);
            errorMessage.textContent = 'An error occurred. Please try again.';
            errorMessage.style.display = 'block';
        }
    });
}); 