// Human Tracking Car Control Interface

class HumanTrackingController {
    constructor() {
        this.isTracking = false;
        this.statusUpdateInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.startStatusUpdates();
        this.loadSettings();
    }

    bindEvents() {
        // Tracking controls
        document.getElementById('startTrackingBtn').addEventListener('click', () => {
            this.startTracking();
        });

        document.getElementById('stopTrackingBtn').addEventListener('click', () => {
            this.stopTracking();
        });

        // Manual controls
        document.querySelectorAll('.direction-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.getAttribute('data-action');
                this.manualControl(action);
            });
        });

        // Speed slider
        document.getElementById('speedSlider').addEventListener('input', (e) => {
            document.getElementById('speedValue').textContent = e.target.value;
        });

        // Settings
        document.getElementById('updateSettingsBtn').addEventListener('click', () => {
            this.updateSettings();
        });

        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
        });

        document.addEventListener('keyup', (e) => {
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 's', 'a', 'd'].includes(e.key)) {
                this.manualControl('stop');
            }
        });
    }

    handleKeyboard(e) {
        if (this.isTracking) return; // Don't allow manual control during tracking

        const speed = document.getElementById('speedSlider').value;

        switch(e.key) {
            case 'ArrowUp':
            case 'w':
                e.preventDefault();
                this.manualControl('forward', speed);
                break;
            case 'ArrowDown':
            case 's':
                e.preventDefault();
                this.manualControl('backward', speed);
                break;
            case 'ArrowLeft':
            case 'a':
                e.preventDefault();
                this.manualControl('left', speed);
                break;
            case 'ArrowRight':
            case 'd':
                e.preventDefault();
                this.manualControl('right', speed);
                break;
            case ' ':
                e.preventDefault();
                this.manualControl('stop');
                break;
        }
    }

    async startTracking() {
        try {
            const response = await fetch('/api/control/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.isTracking = true;
                this.updateTrackingUI();
                this.showToast('Tracking started', 'success');
            } else {
                this.showToast(result.error || 'Failed to start tracking', 'error');
            }
        } catch (error) {
            this.showToast('Network error: ' + error.message, 'error');
        }
    }

    async stopTracking() {
        try {
            const response = await fetch('/api/control/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (response.ok) {
                this.isTracking = false;
                this.updateTrackingUI();
                this.showToast('Tracking stopped', 'success');
            } else {
                this.showToast(result.error || 'Failed to stop tracking', 'error');
            }
        } catch (error) {
            this.showToast('Network error: ' + error.message, 'error');
        }
    }

    async manualControl(action, speed = null) {
        if (speed === null) {
            speed = document.getElementById('speedSlider').value;
        }

        try {
            const response = await fetch('/api/control/manual', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: action,
                    speed: parseInt(speed)
                })
            });

            const result = await response.json();

            if (!response.ok) {
                this.showToast(result.error || 'Manual control failed', 'error');
            }
        } catch (error) {
            this.showToast('Network error: ' + error.message, 'error');
        }
    }

    async updateSettings() {
        try {
            const settings = {
                target_distance: parseInt(document.getElementById('targetDistance').value),
                pid_x: {
                    kp: parseFloat(document.getElementById('pidKp').value),
                    ki: parseFloat(document.getElementById('pidKi').value),
                    kd: parseFloat(document.getElementById('pidKd').value)
                }
            };

            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            const result = await response.json();

            if (response.ok) {
                this.showToast('Settings updated', 'success');
            } else {
                this.showToast(result.error || 'Failed to update settings', 'error');
            }
        } catch (error) {
            this.showToast('Network error: ' + error.message, 'error');
        }
    }

    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();

            if (response.ok) {
                document.getElementById('targetDistance').value = settings.target_distance;
                document.getElementById('pidKp').value = settings.pid_x.kp;
                document.getElementById('pidKi').value = settings.pid_x.ki;
                document.getElementById('pidKd').value = settings.pid_x.kd;
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    startStatusUpdates() {
        this.statusUpdateInterval = setInterval(() => {
            this.updateStatus();
        }, 1000);
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();

            if (response.ok) {
                this.updateConnectionStatus(true);
                this.updateSystemStatus(status);
                
                // Update tracking state
                this.isTracking = status.tracking.tracking;
                this.updateTrackingUI();
                
            } else {
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (connected) {
            statusElement.innerHTML = '<i class="fas fa-circle"></i> Connected';
            statusElement.classList.remove('disconnected');
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle"></i> Disconnected';
            statusElement.classList.add('disconnected');
        }
    }

    updateSystemStatus(status) {
        // Camera status
        const cameraStatus = status.camera.camera_active ? 'Active' : 'Inactive';
        document.getElementById('cameraStatus').textContent = cameraStatus;

        // Motor status
        const motorStatus = status.motor.is_moving ? 'Moving' : 'Stopped';
        document.getElementById('motorStatus').textContent = motorStatus;

        // Frame rate
        document.getElementById('frameRate').textContent = status.camera.framerate + ' FPS';

        // Detection status
        const hasDetection = status.tracking.last_human_center !== null;
        const detectionStatus = hasDetection ? 'Human Detected' : 'No Detection';
        document.getElementById('detectionStatus').textContent = detectionStatus;

        // Update detection info overlay
        const detectionInfo = document.getElementById('detectionInfo');
        if (hasDetection) {
            const [x, y, height] = status.tracking.last_human_center;
            detectionInfo.textContent = `Human at (${x}, ${y}) - Height: ${height}px`;
        } else {
            detectionInfo.textContent = 'No human detected';
        }

        // Update video overlay for tracking
        const videoContainer = document.querySelector('.video-container');
        if (this.isTracking && hasDetection) {
            videoContainer.classList.add('tracking-active');
        } else {
            videoContainer.classList.remove('tracking-active');
        }
    }

    updateTrackingUI() {
        const trackingState = document.getElementById('trackingState');
        const startBtn = document.getElementById('startTrackingBtn');
        const stopBtn = document.getElementById('stopTrackingBtn');
        const manualControls = document.querySelectorAll('.direction-btn');

        if (this.isTracking) {
            trackingState.textContent = 'Active';
            trackingState.style.color = '#27ae60';
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            // Disable manual controls during tracking
            manualControls.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
            });
        } else {
            trackingState.textContent = 'Stopped';
            trackingState.style.color = '#e74c3c';
            startBtn.disabled = false;
            stopBtn.disabled = true;
            
            // Enable manual controls when not tracking
            manualControls.forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
            });
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        toastContainer.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toastContainer.removeChild(toast);
            }, 300);
        }, 3000);
    }
}

// Initialize the controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new HumanTrackingController();
});

// Handle video stream errors
document.getElementById('videoStream').addEventListener('error', () => {
    console.log('Video stream error - attempting to reload');
    // Reload the video stream after a delay
    setTimeout(() => {
        const videoStream = document.getElementById('videoStream');
        const src = videoStream.src;
        videoStream.src = '';
        videoStream.src = src;
    }, 1000);
});