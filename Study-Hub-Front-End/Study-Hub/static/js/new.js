document.addEventListener('DOMContentLoaded', function() {
    const registrationForm = document.getElementById('registrationForm');
    
    if (registrationForm) {
        registrationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            let isValid = true;
            
            // Clear previous error messages
            const errorMessages = document.querySelectorAll('.error-message');
            errorMessages.forEach(msg => msg.textContent = '');
            
            // Validate fullname
            const fullname = document.getElementById('fullname');
            if (!fullname.value.match(/^[A-Za-z\s]+$/)) {
                document.getElementById('fullname-error').textContent = 'Please enter a valid name (letters and spaces only)';
                isValid = false;
            }

            // Validate email
            const email = document.getElementById('email');
            if (!email.value.match(/^[\w\.-]+@[\w\.-]+\.\w+$/)) {
                document.getElementById('email-error').textContent = 'Please enter a valid email address';
                isValid = false;
            }

            // Validate password
            const password = document.getElementById('password');
            if (password.value.length < 8 || !/\d/.test(password.value)) {
                document.getElementById('password-error').textContent = 'Password must be at least 8 characters long and contain at least one number';
                isValid = false;
            }

            // Validate subject for teachers
            const subject = document.getElementById('subject');
            if (subject && (!subject.value || subject.value.length < 2)) {
                document.getElementById('subject-error').textContent = 'Please enter a valid subject';
                isValid = false;
            }

            if (isValid) {
                // Show loading state
                const submitBtn = registrationForm.querySelector('button[type="submit"]');
                const originalBtnText = submitBtn.textContent;
                submitBtn.textContent = 'Registering...';
                submitBtn.disabled = true;

                // Submit the form
                registrationForm.submit();
            }
        });

        // Clear error messages on input
        const inputs = registrationForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                const errorElement = document.getElementById(`${this.id}-error`);
                if (errorElement) {
                    errorElement.textContent = '';
                }
            });
        });
    }
}); 