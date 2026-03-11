function showForm(type) {
    const loginForm = document.getElementById('form-login');
    const signupForm = document.getElementById('form-signup');
    const btnLogin = document.getElementById('btn-login');
    const btnSignup = document.getElementById('btn-signup');

    if (type === 'login') {
        loginForm.style.display = 'block';
        signupForm.style.display = 'none';
        btnLogin.style.background = 'var(--primary)';
        btnSignup.style.background = 'transparent';
    } else {
        loginForm.style.display = 'none';
        signupForm.style.display = 'block';
        btnLogin.style.background = 'transparent';
        btnSignup.style.background = 'var(--secondary)';
    }
}

function handleGoogleLogin() {
    if (typeof google === 'undefined' || !google.accounts) {
        return;
    }

    google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            const btnContainer = document.querySelector('.g_id_signin');
            if (btnContainer) {
                btnContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
                btnContainer.classList.add('highlight-shake');

                setTimeout(() => {
                    btnContainer.classList.remove('highlight-shake');
                }, 1000);

                const helperText = document.getElementById('login-helper-text');
                if (helperText) {
                    const originalText = helperText.innerHTML;
                    helperText.innerHTML = '<span class="auth-helper-strong">Please tap the main Google button above ☝️</span>';
                    setTimeout(() => {
                        helperText.innerHTML = originalText;
                    }, 3000);
                }
            }
        }
    });
}
