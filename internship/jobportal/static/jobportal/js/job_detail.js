document.addEventListener('DOMContentLoaded', function() {
    
    const shareBtn = document.getElementById('shareBtn');
    
    if (shareBtn) {
        shareBtn.addEventListener('click', function() {
            // Copy current URL to clipboard
            navigator.clipboard.writeText(window.location.href).then(() => {
                const originalText = shareBtn.innerHTML;
                shareBtn.innerHTML = "✓ Copied!";
                shareBtn.style.color = "#059669";
                
                setTimeout(() => {
                    shareBtn.innerHTML = originalText;
                    shareBtn.style.color = "";
                }, 2000);
            });
        });
    }
});