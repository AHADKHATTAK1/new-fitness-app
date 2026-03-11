(function () {
    let deferredPrompt = null;
    const installBtn = document.getElementById('pwa-install-btn');
    const status = document.getElementById('install-status');

    window.addEventListener('beforeinstallprompt', (event) => {
        event.preventDefault();
        deferredPrompt = event;
        if (installBtn) {
            installBtn.classList.remove('install-btn-hidden');
            installBtn.classList.add('install-btn-visible');
        }
        if (status) status.textContent = 'Install is available on this device/browser.';
    });

    if (installBtn) {
        installBtn.addEventListener('click', async () => {
            if (!deferredPrompt) {
                if (status) status.textContent = 'Install prompt not available. Use browser menu install option.';
                return;
            }
            deferredPrompt.prompt();
            const choiceResult = await deferredPrompt.userChoice;
            if (status) {
                status.textContent = choiceResult.outcome === 'accepted'
                    ? 'App install started. Check your home screen/app list.'
                    : 'Install cancelled. You can try again anytime.';
            }
            deferredPrompt = null;
            installBtn.classList.remove('install-btn-visible');
            installBtn.classList.add('install-btn-hidden');
        });
    }
})();
