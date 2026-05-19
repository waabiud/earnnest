// Toggle password visibility
function togglePassword(el) {
    const input = el.closest('.input-icon').querySelector('input');
    const icon = el.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

// Copy referral link
function copyRef() {
    const input = document.getElementById('refLink');
    if (input) {
        navigator.clipboard.writeText(input.value).then(() => {
            showToast('Referral link copied!', 'success');
        });
    }
}

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.4s';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });
});

// Hamburger menu
const hamburger = document.getElementById('hamburger');
if (hamburger) {
    hamburger.addEventListener('click', () => {
        document.querySelector('.nav-links').classList.toggle('open');
    });
}

// Simple toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.innerHTML = `${message} <button class="alert-close" onclick="this.parentElement.remove()">×</button>`;
    let container = document.querySelector('.messages-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages-container';
        document.body.appendChild(container);
    }
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// Poll notification count every 60 seconds
function updateNotifCount() {
    fetch('/notifications/unread/')
        .then(res => res.json())
        .then(data => {
            const badge = document.getElementById('notif-badge');
            if (badge) {
                if (data.count > 0) {
                    badge.style.display = 'flex';
                    badge.textContent = data.count;
                } else {
                    badge.style.display = 'none';
                }
            }
        }).catch(() => {});
}

document.addEventListener('DOMContentLoaded', () => {
    updateNotifCount();
    setInterval(updateNotifCount, 60000);
});