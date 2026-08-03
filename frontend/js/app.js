/**
 * TSRTC Smart Analytics Platform - Main Application
 * Enterprise transport analytics engine
 */

const API_BASE = 'http://localhost:8000';

// ===========================
// AUTHENTICATION
// ===========================

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
    }

    async login(username, password) {
        try {
            console.log('📡 Sending login request to:', `${API_BASE}/api/auth/login`);

            const response = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            console.log('📨 Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ Response error:', errorText);
                throw new Error('Invalid credentials');
            }

            const data = await response.json();
            console.log('✅ Login response data:', data);

            this.token = data.access_token;
            this.user = data.user;

            localStorage.setItem('auth_token', this.token);
            localStorage.setItem('user', JSON.stringify(this.user));

            console.log('💾 Stored in localStorage - token:', this.token.substring(0, 20) + '...', 'user:', this.user);

            return data;
        } catch (error) {
            console.error('🔥 Login error:', error);
            throw error;
        }
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        window.location.href = 'index.html';
    }

    isAuthenticated() {
        return !!this.token;
    }

    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }
}

const auth = new AuthManager();

// ===========================
// API CLIENT
// ===========================

class APIClient {
    constructor() {
        this.baseUrl = API_BASE;
    }
    async uploadData(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return await response.json();
    }

    async getODMatrix(filters = {}) {
        const params = new URLSearchParams(filters);
        const response = await fetch(`${API_BASE}/api/analytics/od-matrix?${params}`);

        if (!response.ok) throw new Error('Failed to fetch OD matrix');
        return await response.json();
    }

    async getProfitability() {
        const response = await fetch(`${API_BASE}/api/analytics/profitability`);
        if (!response.ok) throw new Error('Failed to fetch profitability data');
        return await response.json();
    }

    async runSimulation(params) {
        const response = await fetch(`${API_BASE}/api/simulator/whatif`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });

        if (!response.ok) throw new Error('Simulation failed');
        return await response.json();
    }

    async getGeoData() {
        const response = await fetch(`${API_BASE}/api/geo/stops`);
        if (!response.ok) throw new Error('Failed to fetch geo data');
        return await response.json();
    }

    async downloadSample() {
        window.open(`${API_BASE}/api/sample-csv`, '_blank');
    }

    async exportCSV(reportType) {
        window.open(`${API_BASE}/api/reports/export/csv?report_type=${reportType}`, '_blank');
    }

    async getCrewForBus(busNumber) {
        const response = await fetch(`${API_BASE}/api/complaints/crew/${encodeURIComponent(busNumber)}`);
        if (!response.ok) throw new Error('Failed to fetch crew');
        return await response.json();
    }

    async submitComplaint(body) {
        const response = await fetch(`${API_BASE}/api/complaints/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) throw new Error((await response.json()).detail || 'Submit failed');
        return await response.json();
    }

    async getBookingRoutes() {
        const response = await fetch(`${API_BASE}/api/booking/routes`);
        if (!response.ok) return { routes: [] };
        return await response.json();
    }

    async createBooking(booking) {
        const response = await fetch(`${API_BASE}/api/booking/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(booking)
        });
        if (!response.ok) throw new Error((await response.json()).detail || 'Booking failed');
        return await response.json();
    }

    async createFareBasedBooking(booking) {
        const response = await fetch(`${API_BASE}/api/bookings/fare-based`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(booking)
        });
        if (!response.ok) throw new Error((await response.json()).detail || 'Booking failed');
        return await response.json();
    }

    async getAllComplaints() {
        const response = await fetch(`${API_BASE}/api/complaints/all`, {
            headers: auth.getHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch complaints');
        return await response.json();
    }

    async getBookingHistory(phone, email) {
        const params = new URLSearchParams();
        if (phone) params.set('phone', phone);
        if (email) params.set('email', email);
        const response = await fetch(`${API_BASE}/api/booking/history?${params}`);
        if (!response.ok) return { bookings: [] };
        return await response.json();
    }
}

const api = new APIClient();

// ===========================
// NOTIFICATION SYSTEM
// ===========================

class NotificationManager {
    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.5rem;">
                    ${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}
                </span>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    success(message) {
        this.show(message, 'success');
    }

    error(message) {
        this.show(message, 'error');
    }

    info(message) {
        this.show(message, 'info');
    }
}

const notify = new NotificationManager();

// ===========================
// CHART UTILITIES
// ===========================

class ChartManager {
    constructor() {
        this.charts = {};
    }

    createBarChart(canvasId, labels, data, label, color = '#00d4ff') {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: `${color}33`,
                    borderColor: color,
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#ffffff', font: { size: 12 } }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#a0aec0' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#a0aec0', maxRotation: 45, minRotation: 45 }
                    }
                }
            }
        });
    }

    createLineChart(canvasId, labels, datasets) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets.map(ds => ({
                    ...ds,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#ffffff', font: { size: 12 } }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#a0aec0' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#a0aec0' }
                    }
                }
            }
        });
    }

    createPieChart(canvasId, labels, data, colors) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }

        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#ffffff', padding: 20, font: { size: 12 } }
                    }
                }
            }
        });
    }
}

const chartManager = new ChartManager();

// ===========================
// UTILITY FUNCTIONS
// ===========================

function formatNumber(num) {
    if (num >= 10000000) return (num / 10000000).toFixed(2) + ' Cr';
    if (num >= 100000) return (num / 100000).toFixed(2) + ' L';
    if (num >= 1000) return (num / 1000).toFixed(2) + 'K';
    return num.toFixed(0);
}

function formatCurrency(num) {
    return '₹' + formatNumber(num);
}

function formatPercentage(num) {
    return num.toFixed(2) + '%';
}

function animateValue(element, start, end, duration) {
    if (!element) return;

    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            element.textContent = formatNumber(end);
            clearInterval(timer);
        } else {
            element.textContent = formatNumber(current);
        }
    }, 16);
}

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<div class="spinner"></div>';
    }
}

function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
    }
}

function createModal(title, content) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>${title}</h3>
            <div style="margin-top: 1.5rem;">
                ${content}
            </div>
            <button class="btn btn-secondary mt-3" onclick="this.closest('.modal').remove()">
                Close
            </button>
        </div>
    `;

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });

    document.body.appendChild(modal);
}

// ===========================
// PAGE INITIALIZATION
// ===========================

function initNavigation() {
    const currentPage = window.location.pathname.split('/').pop();
    const navLinks = document.querySelectorAll('.nav-links a');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPage) {
            link.classList.add('active');
        }
    });

    // Add user info
    if (auth.isAuthenticated() && auth.user) {
        const userInfo = document.querySelector('.user-info');
        if (userInfo) {
            userInfo.innerHTML = `
                <span style="color: var(--text-secondary);">${auth.user.username}</span>
                <span class="badge badge-info">${auth.user.role}</span>
            `;
        }
    }
}

// Protect pages
function requireAuth() {
    if (!auth.isAuthenticated()) {
        window.location.href = 'index.html';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();

    // Add animation classes to cards as they load
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach((card, index) => {
        card.style.animation = 'fadeIn 0.6s ease-out forwards';
        card.style.animationDelay = `${index * 0.1}s`;
        card.style.opacity = '0';
    });
});

// Add slide-out animation for toasts
const slideOutKeyframes = `
    @keyframes slideOut {
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
const style = document.createElement('style');
style.textContent = slideOutKeyframes;
document.head.appendChild(style);

// Expose API_BASE for pages that need it
window.API_BASE = API_BASE;
if (window.TSRTC && window.TSRTC.api) {
    window.TSRTC.api.baseUrl = API_BASE;
}

// Export for use in other scripts
window.TSRTC = Object.assign(window.TSRTC || {}, {
    auth,
    api,
    notify,
    chartManager,
    formatNumber,
    formatCurrency,
    formatPercentage,
    animateValue,
    showLoading,
    hideLoading,
    createModal,
    requireAuth
});