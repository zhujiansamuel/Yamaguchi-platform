/**
 * Files sidebar Info tab for data_platform Excel exports.
 */
(function() {
    'use strict';

    const APP_ID = 'onlyoffice_callback_interceptor';
    const TAB_ID = 'onlyoffice-info-tab';
    const DATA_PLATFORM_ROOT = '/data_platform';
    const EXPORT_FILENAME_PATTERN = /_test_\d{8}_\d{6}\.xlsx$/i;

    const isDataPlatformExcel = (fileInfo) => {
        if (!fileInfo || !fileInfo.name) {
            return false;
        }

        const filePath = fileInfo.path || '';
        const isInDataPlatform = filePath === DATA_PLATFORM_ROOT || filePath.startsWith(`${DATA_PLATFORM_ROOT}/`);
        const isExcel = fileInfo.name.toLowerCase().endsWith('.xlsx');
        const matchesExportPattern = EXPORT_FILENAME_PATTERN.test(fileInfo.name);

        return isInDataPlatform && isExcel && matchesExportPattern;
    };

    const renderContent = (container, fileInfo) => {
        container.innerHTML = '';

        const descriptionLabel = document.createElement('label');
        descriptionLabel.className = 'onlyoffice-info-label';
        descriptionLabel.textContent = '说明';

        const descriptionField = document.createElement('textarea');
        descriptionField.className = 'onlyoffice-info-textarea';
        descriptionField.placeholder = fileInfo.name;
        descriptionField.rows = 4;

        const helperText = document.createElement('div');
        helperText.className = 'onlyoffice-info-helper';
        helperText.textContent = '在此处填写文件说明。';

        container.appendChild(descriptionLabel);
        container.appendChild(descriptionField);
        container.appendChild(helperText);
    };

    const registerTab = () => {
        if (!OCA || !OCA.Files || !OCA.Files.Sidebar) {
            return;
        }

        // Create a Tab class compatible with Nextcloud's Sidebar API
        class DataPlatformInfoTab {
            constructor() {
                this.id = TAB_ID;
                this.name = 'Info';
                this.icon = 'icon-info';
                this._isActive = false;
            }

            setIsActive(isActive) {
                this._isActive = isActive;
            }

            enabled(fileInfo) {
                return isDataPlatformExcel(fileInfo);
            }

            mount(el, fileInfo, context) {
                renderContent(el, fileInfo);
            }

            update(fileInfo) {
                // Update is handled by mount
            }

            destroy() {
                // Cleanup if needed
            }

            // Compatibility method - some versions may call canDisplay
            canDisplay(fileInfo) {
                return this.enabled(fileInfo);
            }
        }

        try {
            OCA.Files.Sidebar.registerTab(new DataPlatformInfoTab());
        } catch (error) {
            console.error('[OnlyOffice Callback Interceptor] Failed to register sidebar tab:', error);
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', registerTab);
    } else {
        registerTab();
    }
})();
