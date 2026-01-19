/**
 * Frontend JavaScript for conversational AI webapp.
 * Handles voice recording, text input, and chat interface.
 */

class ChatApp {
    constructor() {
        this.sessionId = null;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.initializeElements();
        this.initializeEventListeners();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chat-messages');
        this.textInput = document.getElementById('text-input');
        this.sendButton = document.getElementById('send-button');
        this.voiceButton = document.getElementById('voice-button');
        this.recordingStatus = document.getElementById('recording-status');
        this.errorMessage = document.getElementById('error-message');
        this.micIcon = document.getElementById('mic-icon');
    }

    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendTextMessage());

        // Enter key to send (Shift+Enter for new line)
        this.textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendTextMessage();
            }
        });

        // Voice button click
        this.voiceButton.addEventListener('click', () => this.toggleVoiceRecording());
    }

    /**
     * Send text message to the backend.
     */
    async sendTextMessage() {
        const message = this.textInput.value.trim();
        if (!message) return;

        // Clear input
        this.textInput.value = '';
        this.sendButton.disabled = true;

        // Display user message
        this.addMessage('user', message);

        try {
            // Send to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Store session ID
            if (data.session_id) {
                this.sessionId = data.session_id;
            }

            // Display AI response
            this.addMessage('assistant', data.response);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Failed to send message. Please try again.');
        } finally {
            this.sendButton.disabled = false;
        }
    }

    /**
     * Toggle voice recording on/off.
     */
    async toggleVoiceRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    /**
     * Start voice recording.
     */
    async startRecording() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                } 
            });

            // Initialize MediaRecorder
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.processAudioRecording();
                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop());
            };

            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
            this.updateRecordingUI(true);

        } catch (error) {
            console.error('Error starting recording:', error);
            this.showError('Failed to access microphone. Please check permissions.');
            this.isRecording = false;
            this.updateRecordingUI(false);
        }
    }

    /**
     * Stop voice recording.
     */
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateRecordingUI(false);
        }
    }

    /**
     * Process recorded audio and send to backend for transcription.
     */
    async processAudioRecording() {
        if (this.audioChunks.length === 0) {
            this.showError('No audio recorded.');
            return;
        }

        // Show processing indicator
        this.addMessage('system', 'Processing voice input...');

        try {
            // Convert audio chunks to blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            
            // Create FormData for file upload
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            // Send to backend for transcription
            const response = await fetch('/api/voice/transcribe', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const transcription = data.transcription;

            if (!transcription) {
                throw new Error('No transcription received');
            }

            // Remove processing message
            this.removeLastSystemMessage();

            // Display transcribed message as user input
            this.addMessage('user', transcription);

            // Send transcribed text to chat API
            const chatResponse = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: transcription,
                    session_id: this.sessionId
                })
            });

            if (!chatResponse.ok) {
                throw new Error(`HTTP error! status: ${chatResponse.status}`);
            }

            const chatData = await chatResponse.json();
            
            // Store session ID
            if (chatData.session_id) {
                this.sessionId = chatData.session_id;
            }

            // Display AI response
            this.addMessage('assistant', chatData.response);

        } catch (error) {
            console.error('Error processing audio:', error);
            this.removeLastSystemMessage();
            this.showError('Failed to process voice input. Please try again.');
        }
    }

    /**
     * Update UI to reflect recording state.
     */
    updateRecordingUI(recording) {
        if (recording) {
            this.voiceButton.classList.add('recording');
            this.recordingStatus.classList.remove('hidden');
        } else {
            this.voiceButton.classList.remove('recording');
            this.recordingStatus.classList.add('hidden');
        }
    }

    /**
     * Add a message to the chat interface.
     */
    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;

        const contentP = document.createElement('p');
        contentP.textContent = content;
        messageDiv.appendChild(contentP);

        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();
        messageDiv.appendChild(timestamp);

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    /**
     * Remove the last system message (used for processing indicators).
     */
    removeLastSystemMessage() {
        const systemMessages = this.chatMessages.querySelectorAll('.system-message');
        if (systemMessages.length > 0) {
            const lastSystemMessage = systemMessages[systemMessages.length - 1];
            if (lastSystemMessage.textContent.includes('Processing')) {
                lastSystemMessage.remove();
            }
        }
    }

    /**
     * Scroll chat to bottom.
     */
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    /**
     * Show error message to user.
     */
    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.classList.remove('hidden');
        
        // Hide error after 5 seconds
        setTimeout(() => {
            this.errorMessage.classList.add('hidden');
        }, 5000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
