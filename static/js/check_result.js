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

let resultsPending = false;
let pendingResults = null;

function viewResults() {
    const year = document.getElementById('year').value;
    const semester = document.getElementById('semester').value;

    if (!year || !semester) {
        alert('Please select both year and semester');
        return;
    }

    // Hide loading overlay and show results container immediately
    document.getElementById('loadingOverlay').style.display = 'none';
    document.getElementById('resultsContainer').style.display = 'block';
    document.getElementById('selectionForm').style.display = 'none';

    // Fetch and display results immediately
    fetchResultsWithCallback(year, semester, (success, results, studentInfo) => {
        displayResults(results);
    });
}

function fetchResultsWithCallback(year, semester, callback) {
    const token = localStorage.getItem('studentToken');
    fetch(`/api/student/results?year=${year}&semester=${semester}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            callback(true, data.results, data.student_info);
        } else {
            callback(false, [], null);
        }
    })
    .catch(error => {
        callback(false, [], null);
    });
}

function displayResults(results) {
    document.getElementById('loadingOverlay').style.display = 'none';
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