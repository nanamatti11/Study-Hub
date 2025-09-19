document.addEventListener('DOMContentLoaded', function() {
    const evaluationForm = document.getElementById('evaluationForm');
    const instructorSelect = document.getElementById('instructor');
    const subjectSelect = document.getElementById('subject');
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');
    
    // Rating system
    const ratings = {
        teaching_quality: 0,
        course_content: 0,
        communication: 0,
        overall_rating: 0
    };
    
    // Load instructors
    loadInstructors();
    
    // Initialize star rating system
    initializeStarRatings();
    
    // Handle form submission
    evaluationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        submitEvaluation();
    });
    
    function loadInstructors() {
        // The browser will automatically send cookies with the request
        fetch('/api/instructors', {
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                instructorSelect.innerHTML = '<option value="">Choose an instructor...</option>';
                data.instructors.forEach(instructor => {
                    const option = document.createElement('option');
                    option.value = instructor.id;
                    option.textContent = `${instructor.fullname} (${instructor.subject})`;
                    instructorSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading instructors:', error);
        });
    }
    
    function initializeStarRatings() {
        const starGroups = document.querySelectorAll('.star-rating');
        
        starGroups.forEach(group => {
            const ratingType = group.getAttribute('data-rating');
            const stars = group.querySelectorAll('.star');
            
            stars.forEach((star, index) => {
                star.addEventListener('click', function() {
                    const value = parseInt(this.getAttribute('data-value'));
                    ratings[ratingType] = value;
                    updateStarDisplay(group, value);
                });
                
                star.addEventListener('mouseover', function() {
                    const value = parseInt(this.getAttribute('data-value'));
                    updateStarDisplay(group, value, true);
                });
            });
            
            group.addEventListener('mouseleave', function() {
                updateStarDisplay(group, ratings[ratingType]);
            });
        });
    }
    
    function updateStarDisplay(group, rating, isHover = false) {
        const stars = group.querySelectorAll('.star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
    }
    
    function submitEvaluation() {
        // Validate required fields
        if (!instructorSelect.value) {
            showError('Please select an instructor');
            return;
        }
        
        if (!subjectSelect.value) {
            showError('Please select a subject');
            return;
        }
        
        // Check if all ratings are provided
        for (const [key, value] of Object.entries(ratings)) {
            if (value === 0) {
                showError('Please provide all ratings');
                return;
            }
        }
        
        const evaluationData = {
            instructor_id: parseInt(instructorSelect.value),
            subject: subjectSelect.value,
            teaching_quality: ratings.teaching_quality,
            course_content: ratings.course_content,
            communication: ratings.communication,
            overall_rating: ratings.overall_rating,
            comments: document.getElementById('comments').value
        };
        
        // The browser will automatically send cookies with the request
        fetch('/api/evaluation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(evaluationData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess('Evaluation submitted successfully!');
                resetForm();
            } else {
                showError(data.message || 'Failed to submit evaluation');
            }
        })
        .catch(error => {
            console.error('Error submitting evaluation:', error);
            showError('An error occurred while submitting evaluation');
        });
    }
    
    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        errorMessage.style.display = 'none';
        setTimeout(() => {
            successMessage.style.display = 'none';
        }, 5000);
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        successMessage.style.display = 'none';
    }
    
    function resetForm() {
        evaluationForm.reset();
        // Reset ratings
        for (const key in ratings) {
            ratings[key] = 0;
        }
        // Reset star displays
        document.querySelectorAll('.star-rating').forEach(group => {
            updateStarDisplay(group, 0);
        });
    }
});
