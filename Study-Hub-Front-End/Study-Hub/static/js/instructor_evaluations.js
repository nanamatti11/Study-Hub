document.addEventListener('DOMContentLoaded', function() {
    loadEvaluations();
    
    function loadEvaluations() {
        const token = localStorage.getItem('instructorToken');
        
        fetch('/api/instructor/evaluations', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayEvaluations(data.evaluations);
                updateStats(data.evaluations);
            } else {
                console.error('Error loading evaluations:', data.message);
            }
        })
        .catch(error => {
            console.error('Error loading evaluations:', error);
        });
    }
    
    function displayEvaluations(evaluations) {
        const evaluationsList = document.getElementById('evaluationsList');
        
        if (evaluations.length === 0) {
            evaluationsList.innerHTML = `
                <div class="no-evaluations">
                    <i class="fas fa-inbox fa-3x"></i>
                    <p>No evaluations yet. Students will be able to provide feedback here.</p>
                </div>
            `;
            return;
        }
        
        evaluationsList.innerHTML = evaluations.map(evaluation => `
            <div class="evaluation-item">
                <div class="evaluation-header">
                    <div class="student-info">
                        <strong>${evaluation.student_name}</strong> - ${evaluation.subject}
                    </div>
                    <div class="evaluation-date">
                        ${new Date(evaluation.created_at).toLocaleDateString()}
                    </div>
                </div>
                
                <div class="ratings-grid">
                    <div class="rating-item">
                        <div class="rating-value">${evaluation.teaching_quality}/5</div>
                        <div class="rating-stars">${generateStars(evaluation.teaching_quality)}</div>
                        <div>Teaching Quality</div>
                    </div>
                    <div class="rating-item">
                        <div class="rating-value">${evaluation.course_content}/5</div>
                        <div class="rating-stars">${generateStars(evaluation.course_content)}</div>
                        <div>Course Content</div>
                    </div>
                    <div class="rating-item">
                        <div class="rating-value">${evaluation.communication}/5</div>
                        <div class="rating-stars">${generateStars(evaluation.communication)}</div>
                        <div>Communication</div>
                    </div>
                    <div class="rating-item">
                        <div class="rating-value">${evaluation.overall_rating}/5</div>
                        <div class="rating-stars">${generateStars(evaluation.overall_rating)}</div>
                        <div>Overall Rating</div>
                    </div>
                </div>
                
                ${evaluation.comments ? `
                    <div class="comments-section">
                        <strong>Comments:</strong>
                        <p>${evaluation.comments}</p>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }
    
    function updateStats(evaluations) {
        const totalEvaluations = evaluations.length;
        const averageRating = totalEvaluations > 0 ? 
            (evaluations.reduce((sum, eval) => sum + eval.overall_rating, 0) / totalEvaluations).toFixed(1) : 0;
        const highestRating = totalEvaluations > 0 ? 
            Math.max(...evaluations.map(eval => eval.overall_rating)) : 0;
        
        document.getElementById('totalEvaluations').textContent = totalEvaluations;
        document.getElementById('averageRating').textContent = averageRating;
        document.getElementById('highestRating').textContent = highestRating;
    }
    
    function generateStars(rating) {
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) {
                stars += '<i class="fas fa-star"></i>';
            } else {
                stars += '<i class="far fa-star"></i>';
            }
        }
        return stars;
    }
});
