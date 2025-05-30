// Check if user is logged in
function checkAuth() {
    const token = localStorage.getItem('instructorToken');
    if (!token) {
        window.location.href = '/';
        return;
    }
}

// Handle logout
function logout() {
    localStorage.removeItem('instructorToken');
    window.location.href = '/';
}

// Add event listeners when document is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    checkAuth();

    // Set up logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Set up feature buttons
    const searchStudentBtn = document.getElementById('searchStudentBtn');
    const addResultBtn = document.getElementById('addResultBtn');
    const manageResultsBtn = document.getElementById('manageResultsBtn');

    if (searchStudentBtn) {
        searchStudentBtn.addEventListener('click', () => {
            window.location.href = '/instructor/search_student';
        });
    }

    if (addResultBtn) {
        addResultBtn.addEventListener('click', () => {
            window.location.href = '/instructor/update_results';
        });
    }

    if (manageResultsBtn) {
        manageResultsBtn.addEventListener('click', () => {
            window.location.href = '/instructor/manage_results';
        });
    }

    // Get instructor name from token
    try {
        const tokenData = JSON.parse(atob(localStorage.getItem('instructorToken').split('.')[1]));
        const instructorName = tokenData.user;
        document.getElementById('instructorName').textContent = `Welcome, ${instructorName}`;
    } catch (error) {
        console.error('Error parsing token:', error);
    }

    // Handle search functionality
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const searchTerm = document.getElementById('searchInput').value;
            
            try {
                const response = await fetch(`/api/students/search?term=${encodeURIComponent(searchTerm)}`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('instructorToken')}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    if (response.status === 401) {
                        // Token is invalid or expired
                        localStorage.removeItem('instructorToken');
                        window.location.href = '/';
                        return;
                    }
                    throw new Error('Network response was not ok');
                }

                const data = await response.json();
                // Handle search results
                console.log('Search results:', data);
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }

    // Handle result submission
    const resultForm = document.getElementById('resultForm');
    if (resultForm) {
        resultForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const resultData = {
                studentId: document.getElementById('studentId').value,
                subject: document.getElementById('subject').value,
                marks: document.getElementById('marks').value
            };

            try {
                const response = await fetch('/api/results', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('instructorToken')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(resultData)
                });

                if (!response.ok) {
                    if (response.status === 401) {
                        // Token is invalid or expired
                        localStorage.removeItem('instructorToken');
                        window.location.href = '/';
                        return;
                    }
                    throw new Error('Network response was not ok');
                }

                const data = await response.json();
                // Handle result submission response
                console.log('Result submission response:', data);
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }
}); 