document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. HANDLE SEARCH BAR ---
    const searchBtn = document.querySelector('.search-btn');
    const searchInput = document.querySelector('.search-input');

    searchBtn.addEventListener('click', () => {
        const query = searchInput.value;
        if(query) {
            // Reload page with ?q=search_term
            window.location.href = `/?q=${query}`;
        }
    });

    // Allow pressing "Enter" key to search
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchBtn.click();
        }
    });

    // --- 2. HANDLE FILTERS ---
    const applyFiltersBtn = document.querySelector('.apply-btn'); // The button in Right Sidebar
    
    if(applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', () => {
            const currentUrl = new URL(window.location.href);
            
            // Check Remote Checkbox
            const remoteCheckbox = document.getElementById('remote');
            if (remoteCheckbox && remoteCheckbox.checked) {
                currentUrl.searchParams.set('remote', 'true');
            } else {
                currentUrl.searchParams.delete('remote');
            }

            // Check Full Time Checkbox
            const fullTimeCheckbox = document.getElementById('fulltime');
            if (fullTimeCheckbox && fullTimeCheckbox.checked) {
                currentUrl.searchParams.set('type', 'Full Time');
            } else {
                currentUrl.searchParams.delete('type');
            }

            // Reload with new filters
            window.location.href = currentUrl.toString();
        });
    }
});