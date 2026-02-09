document.addEventListener('DOMContentLoaded', function() {
    
    // Find all password toggle buttons
    const toggleButtons = document.querySelectorAll('.toggle-password');

    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Prevent form submission
            e.preventDefault();
            
            // Find the input field associated with this button
            // We assume the button is inside the same .form-group wrapper
            const wrapper = this.closest('.form-group');
            const input = wrapper.querySelector('input');
            
            if (input.type === 'password') {
                input.type = 'text';
                this.textContent = '🙈'; // Change icon to closed eye
            } else {
                input.type = 'password';
                this.textContent = '👁️'; // Change icon to open eye
            }
        });
    });
});