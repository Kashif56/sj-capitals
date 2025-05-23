document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const fileUploadContainer = document.getElementById('file-upload-container');
    const fileInput = document.getElementById('screenshot');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeButton = document.getElementById('remove-image');
    
    if (fileUploadContainer) {
        // Click on the container to trigger file input
        fileUploadContainer.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Handle drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUploadContainer.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            fileUploadContainer.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            fileUploadContainer.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            fileUploadContainer.classList.add('border-primary', 'bg-light');
        }
        
        function unhighlight() {
            fileUploadContainer.classList.remove('border-primary', 'bg-light');
        }
        
        // Handle file drop
        fileUploadContainer.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            handleFiles(files);
        }
        
        // Handle file selection
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });
        
        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                if (file.type.match('image.*')) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        imagePreview.src = e.target.result;
                        fileUploadContainer.style.display = 'none';
                        previewContainer.style.display = 'block';
                    }
                    
                    reader.readAsDataURL(file);
                }
            }
        }
        
        // Remove image
        if (removeButton) {
            removeButton.addEventListener('click', function() {
                fileInput.value = '';
                imagePreview.src = '#';
                previewContainer.style.display = 'none';
                fileUploadContainer.style.display = 'block';
            });
        }
    }
    
    // Form validation
    const paymentForm = document.getElementById('payment-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            const amountInput = document.getElementById('amount');
            const screenshotInput = document.getElementById('screenshot');
            
            if (!amountInput.value) {
                e.preventDefault();
                showToast('Please enter the amount paid', 'error');
                return false;
            }
            
            if (!screenshotInput.files || screenshotInput.files.length === 0) {
                e.preventDefault();
                showToast('Please upload a payment screenshot', 'error');
                return false;
            }
            
            return true;
        });
    }
    
    // Custom toast notification
    function showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast show`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const iconClass = type === 'success' ? 'bi-check-circle' : 
                         type === 'warning' ? 'bi-exclamation-triangle' : 
                         type === 'error' ? 'bi-x-circle' : 'bi-info-circle';
        
        const bgClass = type === 'success' ? 'bg-success' : 
                       type === 'warning' ? 'bg-warning' : 
                       type === 'error' ? 'bg-danger' : 'bg-primary';
        
        const title = type === 'success' ? 'Success' : 
                     type === 'warning' ? 'Warning' : 
                     type === 'error' ? 'Error' : 'Information';
        
        toast.innerHTML = `
            <div class="toast-header ${bgClass} text-white">
                <i class="bi ${iconClass} me-2"></i>
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
});
