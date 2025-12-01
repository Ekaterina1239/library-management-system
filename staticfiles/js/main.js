// CSRF token setup for AJAX requests
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// Logout functionality
$(document).on('click', '#logout-btn', function(e) {
    e.preventDefault();

    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/accounts/logout/';
    }
});

// Notification system
function checkUnreadNotifications() {
    $.get('/notifications/api/unread-count/')
        .done(function(data) {
            const badge = $('#notification-badge');
            if (data.unread_count > 0) {
                badge.text(data.unread_count).show();
            } else {
                badge.hide();
            }
        })
        .fail(function(xhr, status, error) {
            console.error('Failed to fetch notifications:', error);
        });
}

// Auto-complete search
function initSearchAutocomplete() {
    const searchInput = $('#search-input');
    if (searchInput.length) {
        let searchTimeout;

        searchInput.on('input', function() {
            clearTimeout(searchTimeout);
            const query = $(this).val();

            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    $.get('/books/api/search/', { q: query })
                        .done(function(data) {
                            // Implement autocomplete dropdown
                            console.log('Search results:', data.results);
                        })
                        .fail(function(xhr, status, error) {
                            console.error('Search failed:', error);
                        });
                }, 300);
            }
        });
    }
}

// Initialize when document is ready
$(document).ready(function() {
    // Check for unread notifications
    if ($('#navbarDropdown').length) {
        checkUnreadNotifications();
        setInterval(checkUnreadNotifications, 60000); // Check every minute
    }

    // Initialize search autocomplete
    initSearchAutocomplete();

    // Add loading states to forms
    $('form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.prop('disabled', true).addClass('loading');
        submitBtn.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...');
    });

    // Tooltip initialization
    $('[data-bs-toggle="tooltip"]').tooltip();

    // Confirm delete actions
    $('.confirm-delete').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
            e.preventDefault();
        }
    });
});

// Utility function for showing notifications
function showNotification(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    $('.container').prepend(alertHtml);

    // Auto remove after 5 seconds
    setTimeout(() => {
        $('.alert').alert('close');
    }, 5000);
}