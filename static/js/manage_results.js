// Check if user is logged in
function checkAuth() {
    const token = localStorage.getItem('instructorToken');
    if (!token) {
        window.location.href = '/';
        return;
    }
}

// Load all results
async function loadResults() {
    try {
        const token = localStorage.getItem('instructorToken');
        const response = await fetch('/api/results', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.results);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('An error occurred while loading results');
    }
}

// Display results in the table
function displayResults(results) {
    const tbody = document.querySelector('#resultsTable tbody');
    tbody.innerHTML = '';

    results.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.student_name}</td>
            <td>${result.subject}</td>
            <td>${result.marks}</td>
            <td>${result.grade}</td>
            <td>${result.credits}</td>
            <td>${result.academic_year}</td>
            <td>${result.semester}</td>
            <td>
                <button onclick="openEditModal(${result.id}, '${result.student_name}', '${result.subject}', ${result.marks}, '${result.grade}', ${result.credits})" class="edit-btn">Edit</button>
                <button onclick="deleteResult(${result.id})" class="delete-btn">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Apply filters
async function applyFilters() {
    const student = document.getElementById('studentFilter').value;
    const subject = document.getElementById('subjectFilter').value;
    const year = document.getElementById('yearFilter').value;
    const semester = document.getElementById('semesterFilter').value;

    try {
        const token = localStorage.getItem('instructorToken');
        const response = await fetch(`/api/results/filter?student=${student}&subject=${subject}&year=${year}&semester=${semester}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        
        if (data.success) {
            displayResults(data.results);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('An error occurred while filtering results');
    }
}

// Open edit modal
function openEditModal(id, studentName, subject, marks, grade, credits) {
    document.getElementById('editResultId').value = id;
    document.getElementById('editStudentName').textContent = studentName;
    document.getElementById('editSubject').textContent = subject;
    document.getElementById('editMarks').value = marks;
    document.getElementById('editGrade').value = grade;
    document.getElementById('editCredits').value = credits;
    document.getElementById('editModal').style.display = 'block';
}

// Close edit modal
function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

// Update result
async function updateResult() {
    const id = document.getElementById('editResultId').value;
    const marks = document.getElementById('editMarks').value;
    const grade = document.getElementById('editGrade').value;
    const credits = document.getElementById('editCredits').value;

    if (!marks || !grade || !credits) {
        showError('Please fill in all fields');
        return;
    }

    try {
        const token = localStorage.getItem('instructorToken');
        const response = await fetch(`/api/results/${id}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ marks, grade, credits })
        });
        const data = await response.json();
        
        if (data.success) {
            closeEditModal();
            loadResults();
            showSuccess('Result updated successfully');
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('An error occurred while updating the result');
    }
}

// Delete result
async function deleteResult(id) {
    if (!confirm('Are you sure you want to delete this result?')) {
        return;
    }

    try {
        const token = localStorage.getItem('instructorToken');
        const response = await fetch(`/api/results/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        
        if (data.success) {
            loadResults();
            showSuccess('Result deleted successfully');
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('An error occurred while deleting the result');
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 3000);
}

// Show success message
function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 3000);
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadResults();

    // Add event listeners
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('closeModal').addEventListener('click', closeEditModal);
    document.getElementById('saveChanges').addEventListener('click', updateResult);
}); 