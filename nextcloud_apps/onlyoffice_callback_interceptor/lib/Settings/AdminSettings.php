<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Settings;

use OCA\OnlyOfficeCallbackInterceptor\Service\ConfigService;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\Settings\ISettings;

/**
 * Admin settings page
 */
class AdminSettings implements ISettings {
    private ConfigService $configService;

    public function __construct(ConfigService $configService) {
        $this->configService = $configService;
    }

    /**
     * @return TemplateResponse
     */
    public function getForm(): TemplateResponse {
        $config = $this->configService->getAll();

        // Convert string booleans to actual booleans for template
        $parameters = [];
        foreach ($config as $key => $value) {
            if ($value === 'true') {
                $parameters[$key] = true;
            } elseif ($value === 'false') {
                $parameters[$key] = false;
            } else {
                $parameters[$key] = $value;
            }
        }

        // Don't show actual secrets in the form (show masked version)
        if (!empty($parameters['onlyoffice_secret'])) {
            $parameters['onlyoffice_secret'] = str_repeat('*', 8);
        }
        if (!empty($parameters['auth_token'])) {
            $parameters['auth_token'] = str_repeat('*', 8);
        }

        return new TemplateResponse(
            'onlyoffice_callback_interceptor',
            'settings/admin',
            $parameters
        );
    }

    /**
     * @return string
     */
    public function getSection(): string {
        return 'onlyoffice-callback';
    }

    /**
     * @return int
     */
    public function getPriority(): int {
        return 50;
    }
}
