/**
 * Admin settings for OnlyOffice Callback Interceptor
 */

(function() {
    'use strict';

    const baseUrl = OC.generateUrl('/apps/onlyoffice_callback_interceptor');

    // Save settings
    document.addEventListener('DOMContentLoaded', function() {
        const saveButton = document.getElementById('save-settings');
        const saveResult = document.getElementById('save-result');
        const testHealthButton = document.getElementById('test-health-check');
        const healthResult = document.getElementById('health-check-result');

        if (saveButton) {
            saveButton.addEventListener('click', function() {
                saveButton.disabled = true;
                saveResult.textContent = 'Saving...';
                saveResult.className = '';

                const data = {
                    django_callback_url: document.getElementById('django_callback_url').value,
                    onlyoffice_secret: document.getElementById('onlyoffice_secret').value,
                    auth_token: document.getElementById('auth_token').value,
                    path_filter: document.getElementById('path_filter').value,
                    enabled: document.getElementById('enabled').checked,
                    debug_mode: document.getElementById('debug_mode').checked,
                    health_check_enabled: document.getElementById('health_check_enabled').checked,
                    health_check_url: document.getElementById('health_check_url').value,
                    health_check_interval: parseInt(document.getElementById('health_check_interval').value, 10),
                    include_user_metadata: document.getElementById('include_user_metadata').checked,
                    include_timestamp: document.getElementById('include_timestamp').checked
                };

                fetch(baseUrl + '/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'requesttoken': OC.requestToken
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(result => {
                    saveButton.disabled = false;

                    if (result.status === 'success') {
                        saveResult.textContent = '✓ Settings saved successfully';
                        saveResult.className = 'success';
                        setTimeout(() => {
                            saveResult.textContent = '';
                        }, 3000);
                    } else {
                        saveResult.textContent = '✗ Error: ' + result.message;
                        saveResult.className = 'error';
                    }
                })
                .catch(error => {
                    saveButton.disabled = false;
                    saveResult.textContent = '✗ Failed to save settings: ' + error.message;
                    saveResult.className = 'error';
                });
            });
        }

        if (testHealthButton) {
            testHealthButton.addEventListener('click', function() {
                testHealthButton.disabled = true;
                healthResult.textContent = 'Testing...';
                healthResult.className = '';

                fetch(baseUrl + '/health-check', {
                    method: 'GET',
                    headers: {
                        'requesttoken': OC.requestToken
                    }
                })
                .then(response => response.json())
                .then(result => {
                    testHealthButton.disabled = false;

                    if (result.status === 'success' && result.health_check) {
                        const hc = result.health_check;

                        if (hc.healthy) {
                            healthResult.textContent = '✓ ' + hc.message;
                            healthResult.className = 'success';
                        } else {
                            healthResult.textContent = '✗ ' + hc.message;
                            healthResult.className = 'error';
                        }

                        setTimeout(() => {
                            healthResult.textContent = '';
                        }, 5000);
                    } else {
                        healthResult.textContent = '✗ Health check failed';
                        healthResult.className = 'error';
                    }
                })
                .catch(error => {
                    testHealthButton.disabled = false;
                    healthResult.textContent = '✗ Error: ' + error.message;
                    healthResult.className = 'error';
                });
            });
        }
    });
})();
