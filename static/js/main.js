/**
 * Blog2Audio - Main JavaScript
 * Handles UI interactions and dynamic functionality
 */

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Flash message handling
    initFlashMessages();
    
    // Input validation
    initFormValidation();
    
    // Initialize audio player enhancements if on the result page
    if (document.getElementById('audio-player')) {
        initAudioPlayer();
    }
    
    // Initialize dark mode toggle
    initDarkMode();
});

/**
 * Initialize flash messages (notifications)
 */
function initFlashMessages() {
    // Close button functionality for flash messages
    const closeButtons = document.querySelectorAll('.close-alert');
    
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.parentElement;
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        });
    });
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(message => {
                message.style.opacity = '0';
                setTimeout(() => {
                    message.style.display = 'none';
                }, 300);
            });
        }, 5000);
    }
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    const urlForm = document.querySelector('form');
    if (!urlForm) return;
    
    urlForm.addEventListener('submit', function(e) {
        const urlInput = document.getElementById('url');
        if (!urlInput) return;
        
        let isValid = true;
        const urlValue = urlInput.value.trim();
        
        // Basic URL validation
        if (!isValidUrl(urlValue)) {
            showInputError(urlInput, 'Please enter a valid URL starting with http:// or https://');
            isValid = false;
        } else {
            removeInputError(urlInput);
        }
        
        if (!isValid) {
            e.preventDefault();
        } else {
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                submitButton.disabled = true;
            }
        }
    });
    
    // Add input event listeners for real-time validation feedback
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.addEventListener('input', function() {
            if (this.value.trim() !== '' && isValidUrl(this.value.trim())) {
                removeInputError(this);
            }
        });
    }
}

/**
 * Check if a string is a valid URL
 * @param {string} url - The URL to validate
 * @returns {boolean} - True if valid URL
 */
function isValidUrl(url) {
    try {
        const parsedUrl = new URL(url);
        return parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:';
    } catch (error) {
        return false;
    }
}

/**
 * Show error message for input field
 * @param {HTMLElement} inputElement - The input element
 * @param {string} message - Error message to display
 */
function showInputError(inputElement, message) {
    // Remove any existing error message
    removeInputError(inputElement);
    
    // Add error styling
    inputElement.classList.add('error');
    
    // Create and append error message
    const errorMessage = document.createElement('div');
    errorMessage.className = 'input-error';
    errorMessage.textContent = message;
    
    // Insert after the input field
    inputElement.parentNode.insertBefore(errorMessage, inputElement.nextSibling);
}

/**
 * Remove error styling and message from input
 * @param {HTMLElement} inputElement - The input element
 */
function removeInputError(inputElement) {
    inputElement.classList.remove('error');
    
    const errorMessage = inputElement.parentNode.querySelector('.input-error');
    if (errorMessage) {
        errorMessage.remove();
    }
}

/**
 * Initialize enhanced audio player features
 */
function initAudioPlayer() {
    const audioPlayer = document.getElementById('audio-player');
    if (!audioPlayer) return;
    
    // Speed control
    const speedControl = document.getElementById('speed');
    if (speedControl) {
        speedControl.addEventListener('change', function() {
            audioPlayer.playbackRate = parseFloat(this.value);
        });
    }
    
    // Volume control
    const volumeControl = document.getElementById('volume');
    if (volumeControl) {
        volumeControl.addEventListener('input', function() {
            audioPlayer.volume = this.value;
        });
        
        // Set initial volume from localStorage if available
        const savedVolume = localStorage.getItem('audioPlayerVolume');
        if (savedVolume) {
            const volume = parseFloat(savedVolume);
            audioPlayer.volume = volume;
            volumeControl.value = volume;
        }
        
        // Save volume setting
        volumeControl.addEventListener('change', function() {
            localStorage.setItem('audioPlayerVolume', this.value);
        });
    }
    
    // Track progress and remember position
    const contentId = audioPlayer.dataset.contentId;
    if (contentId) {
        // Load saved position if available
        const savedPosition = localStorage.getItem(`audioPosition_${contentId}`);
        if (savedPosition) {
            audioPlayer.currentTime = parseFloat(savedPosition);
        }
        
        // Save position periodically
        setInterval(() => {
            if (!audioPlayer.paused) {
                localStorage.setItem(`audioPosition_${contentId}`, audioPlayer.currentTime);
            }
        }, 5000);
        
        // Save position on pause
        audioPlayer.addEventListener('pause', function() {
            localStorage.setItem(`audioPosition_${contentId}`, audioPlayer.currentTime);
        });
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Only process if we're not in an input field
        if (e.target.tagName.toLowerCase() === 'input' || 
            e.target.tagName.toLowerCase() === 'textarea') {
            return;
        }
        
        switch(e.key) {
            case ' ': // Space - play/pause
                e.preventDefault();
                if (audioPlayer.paused) {
                    audioPlayer.play();
                } else {
                    audioPlayer.pause();
                }
                break;
            case 'ArrowLeft': // Left arrow - rewind 10s
                e.preventDefault();
                audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 10);
                break;
            case 'ArrowRight': // Right arrow - forward 10s
                e.preventDefault();
                audioPlayer.currentTime = Math.min(audioPlayer.duration, audioPlayer.currentTime + 10);
                break;
        }
    });
    
    // Handle share modal
    const shareBtn = document.getElementById('share-btn');
    const shareModal = document.getElementById('share-modal');
    const closeModal = document.querySelector('.close');
    
    if (shareBtn && shareModal) {
        shareBtn.addEventListener('click', function() {
            shareModal.style.display = 'block';
        });
        
        if (closeModal) {
            closeModal.addEventListener('click', function() {
                shareModal.style.display = 'none';
            });
        }
        
        window.addEventListener('click', function(event) {
            if (event.target === shareModal) {
                shareModal.style.display = 'none';
            }
        });
        
        // Copy link functionality
        const copyLinkBtn = document.getElementById('copy-link-btn');
        const shareUrl = document.getElementById('share-url');
        
        if (copyLinkBtn && shareUrl) {
            copyLinkBtn.addEventListener('click', function() {
                shareUrl.select();
                document.execCommand('copy');
                
                // Show feedback
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                this.classList.add('copied');
                
                setTimeout(() => {
                    this.textContent = originalText;
                    this.classList.remove('copied');
                }, 2000);
            });
        }
    }
}

/**
 * Initialize dark mode functionality
 */
function initDarkMode() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (!darkModeToggle) return;
    
    // Check for saved theme preference or system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-theme');
        darkModeToggle.checked = true;
    }
    
    // Handle toggle changes
    darkModeToggle.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        }
    });
}