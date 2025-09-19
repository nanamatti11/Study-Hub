document.addEventListener('DOMContentLoaded', function() {
    // Load future tests from API
    loadFutureTests();

    // Handle back button
    document.querySelector('.btn-back').addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = '/student/dashboard';
    });
});

async function loadFutureTests() {
    const loadingAnimation = document.getElementById('loadingAnimation');
    const testsDisplay = document.getElementById('testsDisplay');

    try {
        const response = await fetch('/api/student/future-tests', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token expired or invalid
                window.location.href = '/';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (data.success) {
            displayTests(data.tests);
        } else {
            showError(data.message || 'Failed to load future tests');
        }
    } catch (error) {
        console.error('Error loading future tests:', error);
        showError('Failed to load future tests. Please try again later.');
    } finally {
        loadingAnimation.style.display = 'none';
        testsDisplay.style.display = 'block';
    }
}

function displayTests(tests) {
    const testsDisplay = document.getElementById('testsDisplay');
    
    if (tests.length === 0) {
        testsDisplay.innerHTML = `
            <div class="info-item">
                <div class="info-date">No Tests Scheduled</div>
                <div class="info-title">All Clear!</div>
                <div class="info-details">
                    <div class="detail-item">
                        <i class="fas fa-calendar-check"></i> You have no upcoming tests at the moment
                    </div>
                    <div class="detail-item">
                        <i class="fas fa-info-circle"></i> Check back later for updates
                    </div>
                </div>
            </div>
        `;
        return;
    }

    testsDisplay.innerHTML = tests.map(test => {
        const testDate = new Date(test.date);
        const formattedDate = testDate.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        const formattedTime = formatTime(test.time);

        return `
            <div class="info-item">
                <div class="info-date">${formattedDate}</div>
                <div class="info-title">${escapeHtml(test.subject)}</div>
                <div class="info-details">
                    <div class="detail-item">
                        <i class="fas fa-clock"></i> ${formattedTime} - ${escapeHtml(test.duration)}
                    </div>
                    ${test.location ? `
                        <div class="detail-item">
                            <i class="fas fa-map-marker-alt"></i> ${escapeHtml(test.location)}
                        </div>
                    ` : ''}
                    ${test.test_type ? `
                        <div class="detail-item">
                            <i class="fas fa-book"></i> ${escapeHtml(test.test_type)}
                        </div>
                    ` : ''}
                    ${test.description ? `
                        <div class="detail-item">
                            <i class="fas fa-info-circle"></i> ${escapeHtml(test.description)}
                        </div>
                    ` : ''}
                    ${test.instructor_name ? `
                        <div class="detail-item">
                            <i class="fas fa-user-tie"></i> Instructor: ${escapeHtml(test.instructor_name)}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

function formatTime(timeString) {
    try {
        const [hours, minutes] = timeString.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        return `${displayHour}:${minutes} ${ampm}`;
    } catch (error) {
        return timeString;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const testsDisplay = document.getElementById('testsDisplay');
    testsDisplay.innerHTML = `
        <div class="info-item">
            <div class="info-date">Error</div>
            <div class="info-title">Unable to Load Tests</div>
            <div class="info-details">
                <div class="detail-item">
                    <i class="fas fa-exclamation-triangle"></i> ${escapeHtml(message)}
                </div>
                <div class="detail-item">
                    <i class="fas fa-refresh"></i> Please refresh the page to try again
                </div>
            </div>
        </div>
    `;
}