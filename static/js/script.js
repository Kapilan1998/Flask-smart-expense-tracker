// Global variable to store delete URL
let deleteUrl = null;

// Enhanced page initialization
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to main content
    const mainContent = document.querySelector('.container');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }

    // Enhanced active link detection
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    // Remove active class from all links
    navLinks.forEach(link => {
        link.classList.remove('active');
        
        // Check if this link's href matches current path
        const linkPath = link.getAttribute('href');
        
        // Exact match
        if (linkPath === currentPath) {
            link.classList.add('active');
        }
        
        // Dashboard/home page match
        if (currentPath === '/' && linkPath === '/dashboard') {
            link.classList.add('active');
        }
        
        // Partial match for subpages
        if (linkPath !== '/' && currentPath.startsWith(linkPath) && linkPath !== '/') {
            link.classList.add('active');
        }
    });

    // Format currency display
    const currencyElements = document.querySelectorAll('.currency');
    currencyElements.forEach(el => {
        const value = parseFloat(el.textContent);
        el.textContent = value.toLocaleString('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    });

    // Setup delete buttons to show modal instead of alert
    setupDeleteButtons();

    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 500);
        });
    }, 5000);

    // Initialize Bootstrap components
    initializeBootstrapComponents();
});

// Setup delete buttons with modal confirmation
function setupDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.delete-btn');
    
    deleteButtons.forEach(button => {
        // Remove any existing click handlers
        button.replaceWith(button.cloneNode(true));
    });
    
    // Re-select buttons after cloning
    const newDeleteButtons = document.querySelectorAll('.delete-btn');
    
    newDeleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get the delete URL from href or data attribute
            deleteUrl = this.getAttribute('href');
            const itemType = this.getAttribute('data-type') || 'item';
            const itemName = this.getAttribute('data-name') || 'this item';
            
            // Show delete confirmation modal
            showDeleteModal(itemType, itemName, deleteUrl);
        });
    });
}

// Show delete confirmation modal
function showDeleteModal(itemType, itemName, url) {
    // Create modal HTML if it doesn't exist
    if (!document.getElementById('deleteConfirmationModal')) {
        createDeleteModal();
    }
    
    // Update modal content
    const modal = document.getElementById('deleteConfirmationModal');
    const modalTitle = modal.querySelector('.modal-title');
    const modalBody = modal.querySelector('.modal-body p');
    
    modalTitle.textContent = `Delete ${itemType.charAt(0).toUpperCase() + itemType.slice(1)}`;
    modalBody.textContent = `Are you sure you want to delete "${itemName}"? This action cannot be undone.`;
    
    // Store the delete URL
    deleteUrl = url;
    
    // Show the modal
    const deleteModal = new bootstrap.Modal(modal);
    deleteModal.show();
}

// Create delete confirmation modal
function createDeleteModal() {
    const modalHTML = `
    <div class="modal fade delete-modal" id="deleteConfirmationModal" tabindex="-1" aria-labelledby="deleteModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="deleteModalLabel">Delete Item</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="warning-icon">
                        <i class="bi bi-exclamation-triangle-fill"></i>
                    </div>
                    <h4 class="text-danger mb-3">Warning!</h4>
                    <p class="mb-0">Are you sure you want to delete this item? This action cannot be undone.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary btn-cancel" data-bs-dismiss="modal">
                        <i class="bi bi-x-circle me-2"></i>Cancel
                    </button>
                    <button type="button" class="btn btn-danger btn-confirm" id="confirmDeleteBtn">
                        <i class="bi bi-trash me-2"></i>Delete
                    </button>
                </div>
            </div>
        </div>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add event listener to confirm button
    document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
        if (deleteUrl) {
            // Add loading state
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Deleting...';
            this.disabled = true;
            
            // Redirect to delete URL after a short delay for visual feedback
            setTimeout(() => {
                window.location.href = deleteUrl;
            }, 500);
        }
    });
}

// Initialize Bootstrap components
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}