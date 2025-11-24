document.addEventListener('DOMContentLoaded', function() {
    const urlInput = document.getElementById('url-input');
    const downloadBtn = document.getElementById('download-btn');
    const loading = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    const result = document.getElementById('result');
    const mediaContainer = document.getElementById('media-container');
    const downloadLink = document.getElementById('download-link');
    
    // Function to show loading
    function showLoading() {
        loading.classList.remove('hidden');
        errorMessage.classList.add('hidden');
        result.classList.add('hidden');
    }
    
    // Function to hide loading
    function hideLoading() {
        loading.classList.add('hidden');
    }
    
    // Function to show error
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
        loading.classList.add('hidden');
        result.classList.add('hidden');
    }
    
    // Function to show result
    function showResult(mediaUrl, mediaType) {
        mediaContainer.innerHTML = '';
        
        if (mediaType === 'video') {
            const video = document.createElement('video');
            video.src = mediaUrl;
            video.controls = true;
            video.autoplay = false;
            video.muted = true;
            video.classList.add('media-element');
            mediaContainer.appendChild(video);
        } else {
            const img = document.createElement('img');
            img.src = mediaUrl;
            img.alt = 'Instagram Media';
            img.classList.add('media-element');
            mediaContainer.appendChild(img);
        }
        
        downloadLink.href = mediaUrl;
        downloadLink.download = `instagram-${mediaType}-${Date.now()}`;
        
        result.classList.remove('hidden');
        loading.classList.add('hidden');
        errorMessage.classList.add('hidden');
    }
    
    // Handle download button click
    downloadBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        const url = urlInput.value.trim();
        
        if (!url) {
            showError('Please enter an Instagram URL');
            return;
        }
        
        // Validate URL format
        if (!isValidInstagramUrl(url)) {
            showError('Please enter a valid Instagram URL');
            return;
        }
        
        showLoading();
        
        // Send request to backend
        fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showResult(data.media_url, data.media_type);
            } else {
                showError(data.error || 'Failed to download media');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('An error occurred. Please try again.');
        });
    });
    
    // Handle Enter key in input field
    urlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            downloadBtn.click();
        }
    });
    
    // Function to validate Instagram URL
    function isValidInstagramUrl(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname.includes('instagram.com') || urlObj.hostname.includes('instagr.am');
        } catch (e) {
            return false;
        }
    }
    
    // Auto-validate URL as user types
    urlInput.addEventListener('input', function() {
        const url = urlInput.value.trim();
        if (url && !isValidInstagramUrl(url)) {
            urlInput.style.borderColor = '#c33';
        } else {
            urlInput.style.borderColor = '#eee';
        }
    });
});