document.addEventListener('DOMContentLoaded', function() {
    loadStudentInfo();
    loadLearningResources();
});

function loadStudentInfo() {
    const token = localStorage.getItem('studentToken');
    if (!token) {
        window.location.href = '/';
        return;
    }

    fetch('/api/student/info', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const info = data.student_info;
            document.getElementById('studentName').textContent = `Name: ${info.name}`;
            document.getElementById('studentId').textContent = `ID: ${info.id}`;
        } else {
            window.location.href = '/';
        }
    })
    .catch(() => {
        window.location.href = '/';
    });
}

function loadLearningResources() {
    const token = localStorage.getItem('studentToken');
    
    // Show loading animation
    document.getElementById('loadingAnimation').style.display = 'flex';
    document.getElementById('resourcesDisplay').style.display = 'none';

    // Simulate loading time (5 seconds)
    setTimeout(() => {
        fetch('/api/student/resources', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading animation
            document.getElementById('loadingAnimation').style.display = 'none';
            document.getElementById('resourcesDisplay').style.display = 'block';

            if (data.success) {
                displayResources(data.resources);
            } else {
                document.querySelector('.resources-grid').innerHTML = 
                    `<p class="error">${data.message || 'Failed to load resources'}</p>`;
            }
        })
        .catch(error => {
            document.getElementById('loadingAnimation').style.display = 'none';
            document.getElementById('resourcesDisplay').style.display = 'block';
            document.querySelector('.resources-grid').innerHTML = 
                '<p class="error">An error occurred while loading resources</p>';
        });
    }, 5000);
}

function displayResources(resources) {
    const resourcesGrid = document.querySelector('.resources-grid');
    
    if (resources.length === 0) {
        resourcesGrid.innerHTML = '<p class="no-resources">No learning resources available.</p>';
        return;
    }

    let html = '';
    resources.forEach(resource => {
        html += `
        <div class="resource-card">
            <h3>${resource.title}</h3>
            <p>${resource.description}</p>
            <div class="resource-actions">
                <a href="${resource.link}" target="_blank" class="btn-resource">
                    <i class="fas fa-external-link-alt"></i> View Resource
                </a>
            </div>
        </div>`;
    });

    resourcesGrid.innerHTML = html;
}

function backToDashboard() {
    window.location.href = '/student/dashboard';
} 