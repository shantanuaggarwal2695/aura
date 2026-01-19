/**
 * Admin Panel JavaScript
 * Handles authentication, stats display, and conversation downloads
 */

class AdminPanel {
    constructor() {
        this.adminKey = null;
        this.isAuthenticated = false;
        this.initializeElements();
        this.initializeEventListeners();
    }

    initializeElements() {
        this.adminKeyInput = document.getElementById('admin-key-input');
        this.loginButton = document.getElementById('login-button');
        this.adminContent = document.getElementById('admin-content');
        this.errorMessage = document.getElementById('error-message');
        
        // Stats elements
        this.totalSessions = document.getElementById('total-sessions');
        this.totalMessages = document.getElementById('total-messages');
        this.userMessages = document.getElementById('user-messages');
        this.assistantMessages = document.getElementById('assistant-messages');
        this.refreshStatsButton = document.getElementById('refresh-stats');
        
        // Export elements
        this.downloadCsvButton = document.getElementById('download-csv');
        this.downloadJsonButton = document.getElementById('download-json');
        
        // Preview elements
        this.loadConversationsButton = document.getElementById('load-conversations');
        this.conversationCount = document.getElementById('conversation-count');
        this.conversationsList = document.getElementById('conversations-list');
    }

    initializeEventListeners() {
        // Login
        this.loginButton.addEventListener('click', () => this.login());
        this.adminKeyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.login();
            }
        });

        // Stats refresh
        this.refreshStatsButton.addEventListener('click', () => this.loadStats());

        // Downloads
        this.downloadCsvButton.addEventListener('click', () => this.downloadCsv());
        this.downloadJsonButton.addEventListener('click', () => this.downloadJson());

        // Load conversations
        this.loadConversationsButton.addEventListener('click', () => this.loadConversations());
    }

    /**
     * Login to admin panel
     */
    async login() {
        const key = this.adminKeyInput.value.trim();
        if (!key) {
            this.showError('Please enter an admin key');
            return;
        }

        this.adminKey = key;
        
        // Test authentication by loading stats
        try {
            await this.loadStats();
            this.isAuthenticated = true;
            this.adminContent.classList.remove('hidden');
            this.adminKeyInput.style.display = 'none';
            this.loginButton.textContent = '✓ Authenticated';
            this.loginButton.disabled = true;
        } catch (error) {
            this.showError('Invalid admin key. Please try again.');
            this.adminKey = null;
        }
    }

    /**
     * Load statistics
     */
    async loadStats() {
        try {
            const url = `/api/admin/stats?admin_key=${encodeURIComponent(this.adminKey || '')}`;
            const response = await fetch(url);

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Unauthorized: Invalid admin key');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Update stats display
            this.totalSessions.textContent = data.total_sessions || 0;
            this.totalMessages.textContent = data.total_messages || 0;
            this.userMessages.textContent = data.user_messages || 0;
            this.assistantMessages.textContent = data.assistant_messages || 0;
            
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showError(`Failed to load stats: ${error.message}`);
            throw error;
        }
    }

    /**
     * Download conversations as CSV
     */
    async downloadCsv() {
        if (!this.adminKey) {
            this.showError('Please login first');
            return;
        }

        try {
            this.downloadCsvButton.disabled = true;
            this.downloadCsvButton.innerHTML = '<span class="loading"></span> Downloading...';

            const url = `/api/admin/download/csv?admin_key=${encodeURIComponent(this.adminKey)}`;
            const response = await fetch(url);

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Unauthorized: Invalid admin key');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Get filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = contentDisposition
                ? contentDisposition.split('filename=')[1].replace(/"/g, '')
                : `aura_conversations_${new Date().toISOString()}.csv`;

            // Download file
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);

            this.showError('CSV downloaded successfully!', 'success');
        } catch (error) {
            console.error('Error downloading CSV:', error);
            this.showError(`Failed to download CSV: ${error.message}`);
        } finally {
            this.downloadCsvButton.disabled = false;
            this.downloadCsvButton.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Download CSV
            `;
        }
    }

    /**
     * Download conversations as JSON
     */
    async downloadJson() {
        if (!this.adminKey) {
            this.showError('Please login first');
            return;
        }

        try {
            this.downloadJsonButton.disabled = true;
            this.downloadJsonButton.innerHTML = '<span class="loading"></span> Downloading...';

            const url = `/api/admin/download/json?admin_key=${encodeURIComponent(this.adminKey)}`;
            const response = await fetch(url);

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Unauthorized: Invalid admin key');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Get filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = contentDisposition
                ? contentDisposition.split('filename=')[1].replace(/"/g, '')
                : `aura_conversations_${new Date().toISOString()}.json`;

            // Download file
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);

            this.showError('JSON downloaded successfully!', 'success');
        } catch (error) {
            console.error('Error downloading JSON:', error);
            this.showError(`Failed to download JSON: ${error.message}`);
        } finally {
            this.downloadJsonButton.disabled = false;
            this.downloadJsonButton.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Download JSON
            `;
        }
    }

    /**
     * Load conversations for preview
     */
    async loadConversations() {
        if (!this.adminKey) {
            this.showError('Please login first');
            return;
        }

        try {
            this.loadConversationsButton.disabled = true;
            this.loadConversationsButton.textContent = 'Loading...';
            this.conversationsList.innerHTML = '<p class="empty-state">Loading conversations...</p>';

            const url = `/api/admin/conversations?admin_key=${encodeURIComponent(this.adminKey)}`;
            const response = await fetch(url);

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Unauthorized: Invalid admin key');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const conversations = data.conversations || [];

            // Update count badge
            this.conversationCount.textContent = `${conversations.length} conversations`;

            // Display conversations
            if (conversations.length === 0) {
                this.conversationsList.innerHTML = '<p class="empty-state">No conversations found</p>';
            } else {
                this.conversationsList.innerHTML = conversations.map(conv => this.renderConversation(conv)).join('');
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.showError(`Failed to load conversations: ${error.message}`);
            this.conversationsList.innerHTML = '<p class="empty-state">Error loading conversations</p>';
        } finally {
            this.loadConversationsButton.disabled = false;
            this.loadConversationsButton.textContent = 'Load Conversations';
        }
    }

    /**
     * Render a conversation item
     */
    renderConversation(conv) {
        const messages = conv.messages || [];
        const messageItems = messages.map(msg => `
            <div class="message-item ${msg.role}">
                <div><strong>${msg.role === 'user' ? '👤 User' : '🤖 Assistant'}:</strong></div>
                <div>${this.escapeHtml(msg.content)}</div>
                <div class="message-meta">${msg.timestamp || 'No timestamp'}</div>
            </div>
        `).join('');

        return `
            <div class="conversation-item">
                <div class="conversation-header">
                    <span class="session-id">Session: ${conv.session_id_hash}</span>
                    <span class="message-count">${conv.message_count} messages</span>
                </div>
                <div>${messageItems}</div>
            </div>
        `;
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show error message
     */
    showError(message, type = 'error') {
        this.errorMessage.textContent = message;
        this.errorMessage.className = `error-message ${type === 'success' ? 'success' : ''}`;
        this.errorMessage.classList.remove('hidden');

        setTimeout(() => {
            this.errorMessage.classList.add('hidden');
        }, 5000);
    }
}

// Initialize admin panel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AdminPanel();
});
