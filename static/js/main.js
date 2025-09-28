// Main JavaScript for Progressive Enhancements

// Flash message dismissal
function dismissAlert(button) {
    const alert = button.closest('.alert');
    if (alert) {
        alert.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            alert.remove();
        }, 300);
    }
}

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert:not(.alert-persistent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentElement) {
                dismissAlert(alert.querySelector('.alert-close'));
            }
        }, 5000);
    });
});

// Sidebar toggle for mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        if (overlay) overlay.remove();
    } else {
        sidebar.classList.add('open');
        // Create overlay
        const newOverlay = document.createElement('div');
        newOverlay.id = 'sidebar-overlay';
        newOverlay.className = 'sidebar-overlay';
        newOverlay.onclick = toggleSidebar;
        document.body.appendChild(newOverlay);
    }
}

// User menu toggle
function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    if (menu) {
        menu.classList.toggle('show');
    }
}

// Close user menu when clicking outside
document.addEventListener('click', function (event) {
    const userMenu = document.getElementById('userMenu');
    const userMenuToggle = document.querySelector('.user-menu-toggle');

    if (userMenu && userMenuToggle && !userMenuToggle.contains(event.target)) {
        userMenu.classList.remove('show');
    }
});

// Custom Confirm Popup System
function showCustomConfirm(title, message, confirmText = 'Yes', cancelText = 'No', icon = '⚠️') {
    return new Promise((resolve) => {
        // Remove any existing custom confirm
        const existingConfirm = document.getElementById('customConfirm');
        if (existingConfirm) {
            existingConfirm.remove();
        }

        // Create unique IDs to avoid conflicts
        const uniqueId = 'customConfirm_' + Date.now();
        const confirmBtnId = 'confirmBtn_' + Date.now();
        const cancelBtnId = 'cancelBtn_' + Date.now();

        // Create custom confirm popup
        const confirmHtml = `
            <div id="${uniqueId}" class="custom-confirm" style="display: flex;">
                <div class="custom-confirm-content">
                    <div class="custom-confirm-header">
                        <div class="custom-confirm-icon">${icon}</div>
                        <h3 class="custom-confirm-title">${title}</h3>
                        <p class="custom-confirm-message">${message}</p>
                    </div>
                    <div class="custom-confirm-actions">
                        <button id="${confirmBtnId}" class="btn btn-primary">
                            <span class="btn-icon">✓</span>
                            ${confirmText}
                        </button>
                        <button id="${cancelBtnId}" class="btn btn-outline">
                            <span class="btn-icon">✕</span>
                            ${cancelText}
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add to body
        document.body.insertAdjacentHTML('beforeend', confirmHtml);
        document.body.style.overflow = 'hidden';

        const confirmModal = document.getElementById(uniqueId);
        const confirmBtn = document.getElementById(confirmBtnId);
        const cancelBtn = document.getElementById(cancelBtnId);

        // Cleanup function
        const cleanup = () => {
            if (confirmModal && confirmModal.parentNode) {
                confirmModal.parentNode.removeChild(confirmModal);
            }
            document.body.style.overflow = 'auto';
            document.removeEventListener('keydown', handleEscape);
        };

        // Event listeners
        confirmBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            cleanup();
            resolve(true);
        });

        cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            cleanup();
            resolve(false);
        });

        // Close on backdrop click
        confirmModal.addEventListener('click', (e) => {
            if (e.target === confirmModal) {
                e.preventDefault();
                e.stopPropagation();
                cleanup();
                resolve(false);
            }
        });

        // Close on Escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                cleanup();
                resolve(false);
            }
        };
        document.addEventListener('keydown', handleEscape);
    });
}

// Delete confirmation using custom popup
async function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return await showCustomConfirm(
        'Confirm Delete',
        message,
        'Delete',
        'Cancel',
        '🗑️'
    );
}

// Add confirmation to all delete buttons
document.addEventListener('DOMContentLoaded', function () {
    // Wait a bit for dynamic content to load
    setTimeout(() => {
        // Try multiple selectors to catch all delete buttons
        const selectors = [
            'form[action*="delete"] button[type="submit"]',
            '.delete-form button[type="submit"]',
            '.action-btn.delete-btn',
            'button[title="Delete Expense"]'
        ];

        let deleteButtons = [];
        selectors.forEach(selector => {
            const buttons = document.querySelectorAll(selector);
            deleteButtons = deleteButtons.concat(Array.from(buttons));
        });

        // Remove duplicates
        deleteButtons = [...new Set(deleteButtons)];

        deleteButtons.forEach(button => {
            // Remove any existing event listeners by cloning the button
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);

            newButton.addEventListener('click', async function (e) {
                e.preventDefault();
                e.stopPropagation();

                try {
                    const confirmed = await confirmDelete('Are you sure you want to delete this item? This action cannot be undone.');
                    if (confirmed) {
                        this.closest('form').submit();
                    }
                } catch (error) {
                    // Silently handle errors
                }
            });
        });
    }, 100);
});

// Form validation enhancements
document.addEventListener('DOMContentLoaded', function () {
    // Add real-time validation for amount fields
    const amountInputs = document.querySelectorAll('input[type="number"][name="amount"]');
    amountInputs.forEach(input => {
        input.addEventListener('input', function () {
            const value = parseFloat(this.value);
            if (value < 0) {
                this.setCustomValidity('Amount cannot be negative');
            } else if (value > 999999.99) {
                this.setCustomValidity('Amount too large');
            } else {
                this.setCustomValidity('');
            }
        });
    });

    // Set today's date as default for date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = new Date().toISOString().split('T')[0];
        }
    });
});

// Loading states for forms
document.addEventListener('DOMContentLoaded', function () {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.textContent;
                submitBtn.innerHTML = '<span class="btn-loader">⏳</span> Processing...';

                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                }, 10000);
            }
        });
    });
});

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Update sidebar stats if available
function updateSidebarStats(monthlyTotal) {
    const statElement = document.getElementById('monthlyTotal');
    if (statElement && monthlyTotal !== undefined) {
        statElement.textContent = formatCurrency(monthlyTotal);
    }
}

// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function () {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Keyboard navigation for sidebar
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        const sidebar = document.getElementById('sidebar');
        const userMenu = document.getElementById('userMenu');

        if (sidebar && sidebar.classList.contains('open')) {
            toggleSidebar();
        }
        if (userMenu && userMenu.classList.contains('show')) {
            userMenu.classList.remove('show');
        }
    }
});
