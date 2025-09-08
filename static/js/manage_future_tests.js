// Manage Future Tests JavaScript
class FutureTestsManager {
    constructor() {
        this.tests = [];
        this.currentEditId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTests();
        this.setMinDate();
    }

    bindEvents() {
        // Modal events
        document.getElementById('addTestBtn').addEventListener('click', () => this.openModal());
        document.getElementById('closeModal').addEventListener('click', () => this.closeModal());
        document.getElementById('cancelBtn').addEventListener('click', () => this.closeModal());
        document.getElementById('testForm').addEventListener('submit', (e) => this.handleSubmit(e));

        // Delete modal events
        document.getElementById('closeDeleteModal').addEventListener('click', () => this.closeDeleteModal());
        document.getElementById('cancelDeleteBtn').addEventListener('click', () => this.closeDeleteModal());
        document.getElementById('confirmDeleteBtn').addEventListener('click', () => this.confirmDelete());

        // Close modal on backdrop click
        document.getElementById('testModal').addEventListener('click', (e) => {
            if (e.target.id === 'testModal') this.closeModal();
        });
        document.getElementById('deleteModal').addEventListener('click', (e) => {
            if (e.target.id === 'deleteModal') this.closeDeleteModal();
        });
    }

    setMinDate() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('testDate').min = today;
    }

    async loadTests() {
        try {
            this.showLoading();
            const response = await fetch('/api/instructor/future-tests', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.success) {
                this.tests = data.tests;
                this.renderTests();
            } else {
                this.showError(data.message || 'Failed to load tests');
            }
        } catch (error) {
            console.error('Error loading tests:', error);
            this.showError('Failed to load tests. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    showLoading() {
        document.getElementById('loadingIndicator').style.display = 'block';
        document.getElementById('testsContainer').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('loadingIndicator').style.display = 'none';
    }

    renderTests() {
        const testsList = document.getElementById('testsList');
        const testsContainer = document.getElementById('testsContainer');
        const emptyState = document.getElementById('emptyState');

        if (this.tests.length === 0) {
            testsContainer.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        testsContainer.style.display = 'block';
        emptyState.style.display = 'none';

        testsList.innerHTML = this.tests.map(test => this.renderTestItem(test)).join('');
    }

    renderTestItem(test) {
        const testDate = new Date(test.test_date);
        const formattedDate = testDate.toLocaleDateString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });

        const formattedTime = this.formatTime(test.test_time);

        return `
            <div class="test-item">
                <div class="test-info">
                    <div class="test-subject">${this.escapeHtml(test.subject)}</div>
                    <div class="test-datetime">
                        <div><i class="fas fa-calendar"></i> ${formattedDate}</div>
                        <div><i class="fas fa-clock"></i> ${formattedTime}</div>
                    </div>
                    <div class="test-duration">
                        <i class="fas fa-hourglass-half"></i> ${this.escapeHtml(test.duration)}
                    </div>
                    <div class="test-details">
                        ${test.location ? `<div class="test-location"><i class="fas fa-map-marker-alt"></i> ${this.escapeHtml(test.location)}</div>` : ''}
                        ${test.test_type ? `<div class="test-type">${this.escapeHtml(test.test_type)}</div>` : ''}
                        ${test.description ? `<div class="test-description">${this.escapeHtml(test.description)}</div>` : ''}
                    </div>
                </div>
                <div class="test-actions">
                    <button class="btn-edit" onclick="futureTestsManager.editTest(${test.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn-delete" onclick="futureTestsManager.deleteTest(${test.id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `;
    }

    formatTime(timeString) {
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

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    openModal(test = null) {
        const modal = document.getElementById('testModal');
        const modalTitle = document.getElementById('modalTitle');
        const form = document.getElementById('testForm');

        if (test) {
            modalTitle.textContent = 'Edit Test';
            this.currentEditId = test.id;
            this.populateForm(test);
        } else {
            modalTitle.textContent = 'Add New Test';
            this.currentEditId = null;
            form.reset();
            this.setMinDate();
        }

        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        document.getElementById('testModal').style.display = 'none';
        document.body.style.overflow = 'auto';
        document.getElementById('testForm').reset();
        this.currentEditId = null;
    }

    populateForm(test) {
        document.getElementById('subject').value = test.subject;
        document.getElementById('testDate').value = test.test_date;
        document.getElementById('testTime').value = test.test_time;
        document.getElementById('duration').value = test.duration;
        document.getElementById('location').value = test.location || '';
        document.getElementById('testType').value = test.test_type || '';
        document.getElementById('description').value = test.description || '';
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const testData = {
            subject: formData.get('subject'),
            test_date: formData.get('test_date'),
            test_time: formData.get('test_time'),
            duration: formData.get('duration'),
            location: formData.get('location'),
            test_type: formData.get('test_type'),
            description: formData.get('description')
        };

        try {
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

            const url = this.currentEditId 
                ? `/api/instructor/future-tests/${this.currentEditId}`
                : '/api/instructor/future-tests';
            
            const method = this.currentEditId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(testData)
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(data.message);
                this.closeModal();
                await this.loadTests();
            } else {
                this.showError(data.message || 'Failed to save test');
            }
        } catch (error) {
            console.error('Error saving test:', error);
            this.showError('Failed to save test. Please try again.');
        } finally {
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Save Test';
        }
    }

    editTest(testId) {
        const test = this.tests.find(t => t.id === testId);
        if (test) {
            this.openModal(test);
        }
    }

    deleteTest(testId) {
        const test = this.tests.find(t => t.id === testId);
        if (test) {
            this.currentDeleteId = testId;
            document.getElementById('deleteTestDetails').textContent = 
                `${test.subject} - ${test.test_date} at ${this.formatTime(test.test_time)}`;
            document.getElementById('deleteModal').style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }

    closeDeleteModal() {
        document.getElementById('deleteModal').style.display = 'none';
        document.body.style.overflow = 'auto';
        this.currentDeleteId = null;
    }

    async confirmDelete() {
        if (!this.currentDeleteId) return;

        try {
            const confirmBtn = document.getElementById('confirmDeleteBtn');
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

            const response = await fetch(`/api/instructor/future-tests/${this.currentDeleteId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(data.message);
                this.closeDeleteModal();
                await this.loadTests();
            } else {
                this.showError(data.message || 'Failed to delete test');
            }
        } catch (error) {
            console.error('Error deleting test:', error);
            this.showError('Failed to delete test. Please try again.');
        } finally {
            const confirmBtn = document.getElementById('confirmDeleteBtn');
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-trash"></i> Delete Test';
        }
    }

    showMessage(message, type) {
        const container = document.getElementById('messageContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            ${message}
        `;

        container.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }
}

// Initialize the manager when the page loads
let futureTestsManager;
document.addEventListener('DOMContentLoaded', () => {
    futureTestsManager = new FutureTestsManager();
});
