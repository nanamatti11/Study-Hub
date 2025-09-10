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

        fetch(`/api/students/search?query=${encodeURIComponent(searchTerm)}`, {
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
        const semester1Results = document.getElementById('semester1Results');
        const semester2Results = document.getElementById('semester2Results');
        const semester1Section = document.getElementById('semester1Section');
        const semester2Section = document.getElementById('semester2Section');
        const noResultsMessage = document.getElementById('noResultsMessage');

        // Display the first student's information
        if (students.length > 0) {
            const student = students[0];
            studentName.textContent = student.fullname || student.username;
            studentId.textContent = `ID: ${student.id}`;
            studentEmail.textContent = student.email || `${student.username}@example.com`;

            // Clear previous results and hide sections
            semester1Results.innerHTML = '';
            semester2Results.innerHTML = '';
            semester1Section.style.display = 'none';
            semester2Section.style.display = 'none';
            noResultsMessage.style.display = 'none';

            // Fetch and display real course results for this student
            fetch(`/api/results/filter?student=${student.id}` , {
                headers: headers
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.results.length > 0) {
                    // Group results by semester
                    const semester1Data = data.results.filter(result => result.semester == 1);
                    const semester2Data = data.results.filter(result => result.semester == 2);

                    // Display Semester 1 results
                    if (semester1Data.length > 0) {
                        semester1Results.innerHTML = semester1Data.map(result => `
                            <tr>
                                <td>${result.subject}</td>
                                <td>${result.credits}</td>
                                <td>${result.grade}</td>
                                <td>${result.marks}</td>
                            </tr>
                        `).join('');
                        semester1Section.style.display = 'block';
                    }

                    // Display Semester 2 results
                    if (semester2Data.length > 0) {
                        semester2Results.innerHTML = semester2Data.map(result => `
                            <tr>
                                <td>${result.subject}</td>
                                <td>${result.credits}</td>
                                <td>${result.grade}</td>
                                <td>${result.marks}</td>
                            </tr>
                        `).join('');
                        semester2Section.style.display = 'block';
                    }

                    // Show no results message if no data for any semester
                    if (semester1Data.length === 0 && semester2Data.length === 0) {
                        noResultsMessage.style.display = 'block';
                    }
                } else {
                    noResultsMessage.style.display = 'block';
                }
            })
            .catch(() => {
                noResultsMessage.style.display = 'block';
            });

            resultsContainer.style.display = 'block';
        }
    }

    function showMessage(text, type) {
        message.textContent = text;
        message.className = `message ${type}`;
        message.style.display = 'block';
    }
}); 