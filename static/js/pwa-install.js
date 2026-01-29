// PWA Install Prompt Manager
class PWAInstaller {
    constructor() {
        this.deferredPrompt = null;
        this.init();
    }

    init() {
        // Listen for beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('[PWA] Install prompt available');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });

        // Listen for app installed event
        window.addEventListener('appinstalled', () => {
            console.log('[PWA] App installed successfully');
            this.hideInstallButton();
            this.showToast('✅ App installed! Find it on your home screen.');
        });

        // Check if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('[PWA] Running in standalone mode');
            this.hideInstallButton();
        }
    }

    showInstallButton() {
        const installBtn = document.getElementById('pwa-install-btn');
        if (installBtn) {
            installBtn.style.display = 'flex';

            installBtn.addEventListener('click', () => {
                this.promptInstall();
            });
        }
    }

    hideInstallButton() {
        const installBtn = document.getElementById('pwa-install-btn');
        if (installBtn) {
            installBtn.style.display = 'none';
        }
    }

    async promptInstall() {
        if (!this.deferredPrompt) {
            console.log('[PWA] Install prompt not available');
            return;
        }

        // Show install prompt
        this.deferredPrompt.prompt();

        // Wait for user choice
        const { outcome } = await this.deferredPrompt.userChoice;
        console.log('[PWA] User choice:', outcome);

        if (outcome === 'accepted') {
            this.showToast('🎉 Installing app...');
        }

        // Clear prompt
        this.deferredPrompt = null;
        this.hideInstallButton();
    }

    showToast(message) {
        // Create toast if doesn't exist
        let toast = document.getElementById('pwa-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'pwa-toast';
            toast.style.cssText = `
                position: fixed;
                bottom: 80px;
                left: 50%;
                transform: translateX(-50%);
                background: #1f2937;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 10000;
                display: none;
                font-size: 14px;
            `;
            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.style.display = 'block';

        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }
}

// Initialize PWA installer
const pwaInstaller = new PWAInstaller();

// Register Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then((registration) => {
                console.log('[PWA] Service Worker registered:', registration.scope);

                // Check for updates every hour
                setInterval(() => {
                    registration.update();
                }, 3600000);
            })
            .catch((error) => {
                console.error('[PWA] Service Worker registration failed:', error);
            });
    });
}

// Listen for SW updates
navigator.serviceWorker?.addEventListener('controllerchange', () => {
    console.log('[PWA] New Service Worker activated, reloading...');
    window.location.reload();
});

// Check online/offline status
window.addEventListener('online', () => {
    console.log('[PWA] Back online');
    document.body.classList.remove('offline');
    showConnectionStatus('✅ Back online');

    // Trigger background sync
    if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
        navigator.serviceWorker.ready.then((registration) => {
            return registration.sync.register('sync-offline-actions');
        }).catch((err) => console.error('[PWA] Background sync failed:', err));
    }
});

window.addEventListener('offline', () => {
    console.log('[PWA] Offline');
    document.body.classList.add('offline');
    showConnectionStatus('⚠️ You are offline');
});

function showConnectionStatus(message) {
    const statusDiv = document.getElementById('connection-status');
    if (statusDiv) {
        statusDiv.textContent = message;
        statusDiv.style.display = 'block';

        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }
}

console.log('[PWA] Scripts loaded');
