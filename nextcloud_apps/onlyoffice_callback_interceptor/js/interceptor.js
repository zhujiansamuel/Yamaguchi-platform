/**
 * Frontend script to intercept OnlyOffice configuration
 * This script hooks into the browser's fetch API to modify callback URLs
 */

(function() {
    'use strict';

    // Get configuration from server
    const getConfig = async () => {
        try {
            const response = await fetch(OC.generateUrl('/apps/onlyoffice_callback_interceptor/settings'), {
                headers: {
                    'requesttoken': OC.requestToken
                }
            });
            const data = await response.json();
            return data.config;
        } catch (e) {
            console.error('[OnlyOffice Interceptor] Failed to load config:', e);
            return null;
        }
    };

    // Intercept fetch requests
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const [url, options] = args;

        // Call original fetch
        const response = await originalFetch.apply(this, args);

        // Check if this is an OnlyOffice config request
        if (url && (url.includes('/apps/onlyoffice/ajax/config') || url.includes('EditorApi/config'))) {
            console.log('[OnlyOffice Interceptor] Detected config request:', url);

            const config = await getConfig();
            if (!config || config.enabled !== 'true') {
                console.log('[OnlyOffice Interceptor] Interceptor disabled, skipping');
                return response;
            }

            // Clone response to read and modify it
            const clonedResponse = response.clone();
            try {
                const data = await clonedResponse.json();

                // Check if this has callback URL
                if (data && data.editorConfig && data.editorConfig.callbackUrl) {
                    const originalCallback = data.editorConfig.callbackUrl;

                    // Check path filter
                    const filePath = data.document?.title || data.document?.key || '';
                    const pathFilter = config.path_filter || '';

                    if (pathFilter && !filePath.includes(pathFilter)) {
                        console.log('[OnlyOffice Interceptor] File does not match filter:', filePath);
                        return response;
                    }

                    // Build Django callback URL
                    const params = new URLSearchParams({
                        nextcloud_callback: originalCallback
                    });

                    if (filePath) {
                        params.append('file_path', filePath);
                    }

                    if (config.include_user_metadata === 'true') {
                        params.append('user_id', OC.getCurrentUser().uid);
                        params.append('user_display_name', OC.getCurrentUser().displayName || OC.getCurrentUser().uid);
                    }

                    if (config.include_timestamp === 'true') {
                        params.append('edit_start_time', new Date().toISOString());
                    }

                    const djangoUrl = config.django_callback_url;
                    const separator = djangoUrl.includes('?') ? '&' : '?';
                    data.editorConfig.callbackUrl = djangoUrl + separator + params.toString();

                    console.log('[OnlyOffice Interceptor] Modified callback URL');
                    console.log('  Original:', originalCallback);
                    console.log('  New:', data.editorConfig.callbackUrl);

                    // Return modified response
                    return new Response(JSON.stringify(data), {
                        status: response.status,
                        statusText: response.statusText,
                        headers: response.headers
                    });
                }
            } catch (e) {
                console.error('[OnlyOffice Interceptor] Failed to modify response:', e);
            }
        }

        return response;
    };

    console.log('[OnlyOffice Interceptor] Frontend interceptor loaded');
})();
