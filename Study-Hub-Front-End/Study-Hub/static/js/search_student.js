document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const studentResults = document.getElementById('studentResults');
    const message = document.getElementById('message');

    // Check if instructor is logged in
    const token = localStorage.getItem('instructorToken');
    if (!token) {
        window.location.href = '/';
        return;
    }

    // Set up headers for API requests
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };

    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    function performSearch() {
        const searchTerm = searchInput.value.trim();
        if (!searchTerm) {
            showMessage('Please enter a search term', 'error');
            return;
        }

        // Show loading state
        searchBtn.disabled = true;
        searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        message.style.display = 'none';
        studentResults.style.display = 'none';

        fetch(`/api/students/search?term=${encodeURIComponent(searchTerm)}`, {
            headers: headers
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401) {
                    // Token is invalid or expired
                    localStorage.removeItem('instructorToken');
                    window.location.href = '/';
                    return;
                }
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                if (data.students.length === 0) {
                    showMessage('No students found matching your search', 'info');
                } else {
                    displayResults(data.students);
                }
            } else {
                showMessage(data.message || 'An error occurred', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('An error occurred while searching', 'error');
        })
        .finally(() => {
            // Reset button state
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-search"></i> Search';
        });
    }

    function displayResults(students) {
        const resultsContainer = document.getElementById('studentResults');
        const studentName = document.getElementById('studentName');
        const studentId = document.getElementById('studentId');
        const studentEmail = document.getElementById('studentEmail');
        const courseResults = document.getElementById('courseResults');

        // Display the first student's information
        if (students.length > 0) {
            const student = students[0];
            studentName.textContent = student.username;
            studentId.textContent = `ID: ${student.id}`;
            studentEmail.textContent = `${student.username}@example.com`; // Placeholder email

            // Clear previous results
            courseResults.innerHTML = '';

            // Add a placeholder row for course results
            courseResults.innerHTML = `
                <tr>
                    <td colspan="4" class="no-results">No course results available yet</td>
                </tr>
            `;

            resultsContainer.style.display = 'block';
        }
    }

    function showMessage(text, type) {
        message.textContent = text;
        message.className = `message ${type}`;
        message.style.display = 'block';
    }
}); 