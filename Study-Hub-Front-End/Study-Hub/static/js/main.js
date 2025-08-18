document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const studentBtn = document.getElementById('studentBtn');
    const instructorBtn = document.getElementById('instructorBtn');
    const studentLoginForm = document.getElementById('studentLoginForm');
    const instructorLoginForm = document.getElementById('instructorLoginForm');
    const studentForm = document.getElementById('studentForm');
    const instructorForm = document.getElementById('instructorForm');
    const studentLoginError = document.getElementById('studentLoginError');
    const instructorLoginError = document.getElementById('instructorLoginError');
    const studentPasswordToggle = document.getElementById('studentPasswordToggle');
    const instructorPasswordToggle = document.getElementById('instructorPasswordToggle');
    const container = document.querySelector('.container');

    // Hide both forms initially
    if (studentLoginForm) studentLoginForm.style.display = 'none';
    if (instructorLoginForm) instructorLoginForm.style.display = 'none';

    // Function to toggle password visibility
    function togglePasswordVisibility(input, toggleIcon) {
        if (input.type === 'password') {
            input.type = 'text';
            toggleIcon.classList.remove('fa-eye');
            toggleIcon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            toggleIcon.classList.remove('fa-eye-slash');
            toggleIcon.classList.add('fa-eye');
        }
    }

    // Add password toggle functionality
    if (studentPasswordToggle) {
        studentPasswordToggle.addEventListener('click', function() {
            const passwordInput = document.getElementById('studentPassword');
            if (passwordInput) togglePasswordVisibility(passwordInput, this);
        });
    }

    if (instructorPasswordToggle) {
        instructorPasswordToggle.addEventListener('click', function() {
            const passwordInput = document.getElementById('instructorPassword');
            if (passwordInput) togglePasswordVisibility(passwordInput, this);
        });
    }

    // Function to show login form
    function showLoginForm(formToShow, formToHide) {
        if (container) container.style.display = 'none';
        if (formToShow) formToShow.style.display = 'block';
        if (formToHide) formToHide.style.display = 'none';
        
        // Clear any error messages
        if (studentLoginError) studentLoginError.style.display = 'none';
        if (instructorLoginError) instructorLoginError.style.display = 'none';
    }

    // Function to go back to main view
    function goBack() {
        if (container) container.style.display = 'block';
        if (studentLoginForm) studentLoginForm.style.display = 'none';
        if (instructorLoginForm) instructorLoginForm.style.display = 'none';
    }

    // Student button click handler
    if (studentBtn) {
        studentBtn.addEventListener('click', function() {
            showLoginForm(studentLoginForm, instructorLoginForm);
        });
    }

    // Instructor button click handler
    if (instructorBtn) {
        instructorBtn.addEventListener('click', function() {
            showLoginForm(instructorLoginForm, studentLoginForm);
        });
    }

    // Add back button functionality
    function addBackButton(form) {
        if (!form) return;
        
        const backButton = document.createElement('button');
        backButton.className = 'btn btn-back';
        backButton.innerHTML = '<i class="fas fa-arrow-left"></i> Back to Home';
        backButton.style.marginBottom = '20px';
        
        backButton.addEventListener('click', function(e) {
            e.preventDefault();
            goBack();
        });

        form.insertBefore(backButton, form.firstChild);
    }

    // Add back buttons to both forms
    addBackButton(studentLoginForm);
    addBackButton(instructorLoginForm);

    // Student form submission handler
    if (studentForm) {
        studentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('studentUsername')?.value;
            const password = document.getElementById('studentPassword')?.value;

            if (!username || !password) {
                if (studentLoginError) {
                    studentLoginError.textContent = 'Please enter both username and password';
                    studentLoginError.style.display = 'block';
                }
                return;
            }

            // Show loading state
            const submitBtn = studentForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn ? submitBtn.innerHTML : '';
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
                submitBtn.disabled = true;
            }

            fetch('/api/student/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ username, password }),
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Store token in localStorage
                    localStorage.setItem('studentToken', data.token);
                    localStorage.setItem('studentUsername', username);
                    
                    // Redirect to dashboard
                    window.location.href = '/student/dashboard';
                } else {
                    if (studentLoginError) {
                        studentLoginError.textContent = data.message || 'Login failed. Please try again.';
                        studentLoginError.style.display = 'block';
                    }
                    if (submitBtn) {
                        submitBtn.innerHTML = originalBtnText;
                        submitBtn.disabled = false;
                    }
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                if (studentLoginError) {
                    studentLoginError.textContent = 'An error occurred. Please try again.';
                    studentLoginError.style.display = 'block';
                }
                if (submitBtn) {
                    submitBtn.innerHTML = originalBtnText;
                    submitBtn.disabled = false;
                }
            });
        });
    }

    // Instructor form submission handler
    if (instructorForm) {
        instructorForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('instructorUsername')?.value;
            const password = document.getElementById('instructorPassword')?.value;

            if (!username || !password) {
                if (instructorLoginError) {
                    instructorLoginError.textContent = 'Please enter both username and password';
                    instructorLoginError.style.display = 'block';
                }
                return;
            }

            // Show loading state
            const submitBtn = instructorForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn ? submitBtn.innerHTML : '';
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
                submitBtn.disabled = true;
            }

            fetch('/api/instructor/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ username, password }),
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Store token in localStorage
                    localStorage.setItem('instructorToken', data.token);
                    localStorage.setItem('instructorUsername', username);
                    
                    // Redirect to dashboard
                    window.location.href = '/instructor/dashboard';
                } else {
                    if (instructorLoginError) {
                        instructorLoginError.textContent = data.message || 'Login failed. Please try again.';
                        instructorLoginError.style.display = 'block';
                    }
                    if (submitBtn) {
                        submitBtn.innerHTML = originalBtnText;
                        submitBtn.disabled = false;
                    }
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                if (instructorLoginError) {
                    instructorLoginError.textContent = 'An error occurred. Please try again.';
                    instructorLoginError.style.display = 'block';
                }
                if (submitBtn) {
                    submitBtn.innerHTML = originalBtnText;
                    submitBtn.disabled = false;
                }
            });
        });
    }
}); 