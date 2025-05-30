document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    const token = localStorage.getItem('studentToken');
    const username = localStorage.getItem('studentUsername');
    
    if (!token || !username) {
        window.location.href = '/';
        return;
    }

    // Load student info
    loadStudentInfo();
});

function loadStudentInfo() {
    const token = localStorage.getItem('studentToken');

    fetch('/api/student/info', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const info = data.student_info;
            document.getElementById('studentName').textContent = info.name;
            document.getElementById('studentId').textContent = `Student ID: ${info.id}`;
        } else {
            window.location.href = '/';
        }
    })
    .catch(() => {
        window.location.href = '/';
    });
}

function viewResults() {
    const year = document.getElementById('year').value;
    const semester = document.getElementById('semester').value;

    if (!year || !semester) {
        alert('Please select both year and semester');
        return;
    }

    // Show loading overlay
    document.getElementById('loadingOverlay').style.display = 'flex';
    document.getElementById('resultsContainer').style.display = 'none';

    // Simulate loading time (5 seconds)
    setTimeout(() => {
        fetchResults(year, semester);
    }, 5000);
}

function fetchResults(year, semester) {
    const token = localStorage.getItem('studentToken');

    fetch(`/api/student/results?year=${year}&semester=${semester}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading overlay
        document.getElementById('loadingOverlay').style.display = 'none';
        
        // Hide selection form and show results
        document.getElementById('selectionForm').style.display = 'none';
        document.getElementById('resultsContainer').style.display = 'block';

        if (data.success) {
            // Set results title
            document.getElementById('resultsTitle').textContent = `${new Date().getFullYear()} Results - Year ${year}, Semester ${semester}`;
            displayResults(data.results);
        } else {
            document.getElementById('resultsContent').innerHTML = 
                `<p class="error">${data.message || 'Failed to load results'}</p>`;
        }
    })
    .catch(error => {
        document.getElementById('loadingOverlay').style.display = 'none';
        document.getElementById('resultsContent').innerHTML = 
            '<p class="error">An error occurred while loading results</p>';
        document.getElementById('resultsContainer').style.display = 'block';
        document.getElementById('selectionForm').style.display = 'none';
    });
}

function displayResults(results) {
    const container = document.getElementById('resultsContent');
    
    if (results.length === 0) {
        container.innerHTML = '<p>No results found for this semester.</p>';
        return;
    }

    let html = '<table class="results-table">';
    html += `
        <tr>
            <th>Subject</th>
            <th>Marks</th>
            <th>Grade</th>
        </tr>
    `;

    results.forEach(result => {
        html += `
            <tr>
                <td>${result.subject}</td>
                <td>${result.marks}</td>
                <td>${result.grade}</td>
            </tr>
        `;
    });

    html += '</table>';
    container.innerHTML = html;
}

function showSelectionForm() {
    document.getElementById('resultsContainer').style.display = 'none';
    document.getElementById('selectionForm').style.display = 'block';
} 