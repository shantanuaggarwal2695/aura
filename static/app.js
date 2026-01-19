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
        this.microphonePermissionGranted = false;
        this.initializeElements();
        this.initializeEventListeners();
        this.requestMicrophonePermission();
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
     * Check if browser supports microphone access.
     */
    checkMicrophoneSupport() {
        // Check for modern API
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            return true;
        }
        
        // Check for legacy API
        if (navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia) {
            return true;
        }
        
        return false;
    }

    /**
     * Request microphone permission on page load.
     */
    async requestMicrophonePermission() {
        try {
            // Check if getUserMedia is available (modern or legacy)
            if (!this.checkMicrophoneSupport()) {
                console.warn('getUserMedia is not supported in this browser');
                const browserInfo = this.getBrowserInfo();
                this.addMessage('system', `⚠️ Microphone access is not supported in ${browserInfo}. Please use Chrome, Firefox, Safari, or Edge. You can still use text input.`);
                return;
            }

            // Check if we're on HTTPS or localhost (required for microphone access)
            const isSecure = location.protocol === 'https:' || 
                           location.hostname === 'localhost' || 
                           location.hostname === '127.0.0.1' ||
                           location.hostname === '[::1]';
            
            if (!isSecure) {
                console.warn('Microphone access requires HTTPS or localhost');
                this.addMessage('system', '⚠️ Microphone access requires HTTPS or localhost. You can still use text input.');
                return;
            }

            // Show a brief message that we're requesting permission
            const permissionMsg = this.addMessage('system', '🎤 Requesting microphone permission...');
            
            // Small delay to let user see the message
            await new Promise(resolve => setTimeout(resolve, 300));
            
            // Get the getUserMedia function (modern or legacy)
            const getUserMedia = navigator.mediaDevices?.getUserMedia || 
                               navigator.getUserMedia || 
                               navigator.webkitGetUserMedia || 
                               navigator.mozGetUserMedia || 
                               navigator.msGetUserMedia;
            
            // Request microphone access
            const stream = await new Promise((resolve, reject) => {
                const constraints = { 
                    audio: {
                        channelCount: 1,
                        sampleRate: 16000,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    } 
                };
                
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    // Modern API
                    navigator.mediaDevices.getUserMedia(constraints)
                        .then(resolve)
                        .catch(reject);
                } else {
                    // Legacy API (needs different call signature)
                    getUserMedia.call(navigator, constraints, resolve, reject);
                }
            }).catch(err => {
                // Handle specific permission errors
                if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                    console.log('Microphone permission denied by user');
                    return null;
                } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
                    console.log('No microphone found');
                    return null;
                } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
                    console.log('Microphone is in use');
                    return null;
                } else {
                    console.error('Error requesting microphone:', err);
                    return null;
                }
            });

            // Remove the permission request message
            if (permissionMsg && permissionMsg.parentNode) {
                permissionMsg.remove();
            }

            if (stream) {
                // Permission granted - stop the stream immediately
                stream.getTracks().forEach(track => track.stop());
                this.microphonePermissionGranted = true;
                console.log('Microphone permission granted');
                // Show success message briefly
                const successMsg = this.addMessage('system', '✅ Microphone ready! You can now use voice input.');
                setTimeout(() => {
                    if (successMsg && successMsg.parentNode) {
                        successMsg.style.opacity = '0';
                        successMsg.style.transition = 'opacity 0.5s';
                        setTimeout(() => successMsg.remove(), 500);
                    }
                }, 2000);
            } else {
                this.microphonePermissionGranted = false;
                this.addMessage('system', '⚠️ Microphone permission not granted. You can still use text input, or click the microphone button to try again.');
            }
        } catch (error) {
            console.error('Error requesting microphone permission:', error);
            this.microphonePermissionGranted = false;
            this.addMessage('system', '⚠️ Could not access microphone. You can still use text input.');
        }
    }

    /**
     * Get browser information for error messages.
     */
    getBrowserInfo() {
        const userAgent = navigator.userAgent;
        if (userAgent.indexOf('Chrome') > -1) return 'this version of Chrome';
        if (userAgent.indexOf('Firefox') > -1) return 'this version of Firefox';
        if (userAgent.indexOf('Safari') > -1) return 'this version of Safari';
        if (userAgent.indexOf('Edge') > -1) return 'this version of Edge';
        if (userAgent.indexOf('Opera') > -1) return 'this version of Opera';
        return 'your browser';
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
            // Check if getUserMedia is available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('getUserMedia is not supported in this browser');
            }

            // Check if we're on HTTPS or localhost (required for microphone access)
            const isSecure = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
            if (!isSecure) {
                throw new Error('HTTPS_REQUIRED');
            }

            // Request microphone access (even if we requested on load, we need a new stream for recording)
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            }).catch(err => {
                // Handle specific permission errors
                if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                    throw new Error('PERMISSION_DENIED');
                } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
                    throw new Error('NO_MICROPHONE');
                } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
                    throw new Error('MICROPHONE_IN_USE');
                } else {
                    throw err;
                }
            });

            // Initialize MediaRecorder with fallback mime types
            let mimeType = 'audio/webm;codecs=opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/mp4';
                }
            }

            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: mimeType
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

            this.mediaRecorder.onerror = (event) => {
                console.error('MediaRecorder error:', event.error);
                this.stopRecording();
                this.showError('Recording error occurred. Please try again.');
            };

            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
            this.updateRecordingUI(true);

        } catch (error) {
            console.error('Error starting recording:', error);
            this.isRecording = false;
            this.updateRecordingUI(false);
            
            // Provide specific error messages
            let errorMessage = 'Failed to access microphone. ';
            if (error.message === 'PERMISSION_DENIED') {
                errorMessage += 'Please allow microphone access in your browser settings and try again.';
            } else if (error.message === 'NO_MICROPHONE') {
                errorMessage += 'No microphone found. Please connect a microphone and try again.';
            } else if (error.message === 'MICROPHONE_IN_USE') {
                errorMessage += 'Microphone is being used by another application. Please close it and try again.';
            } else if (error.message === 'HTTPS_REQUIRED') {
                errorMessage += 'Microphone access requires HTTPS. Please use https:// or localhost.';
            } else if (error.message.includes('getUserMedia is not supported')) {
                errorMessage += 'Your browser does not support microphone access. Please use a modern browser.';
            } else {
                errorMessage += 'Please check your browser permissions and try again.';
            }
            
            this.showError(errorMessage);
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
        
        return messageDiv; // Return the element so it can be removed later if needed
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
