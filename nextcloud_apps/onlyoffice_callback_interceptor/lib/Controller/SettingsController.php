<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Controller;

use OCA\OnlyOfficeCallbackInterceptor\Service\ConfigService;
use OCA\OnlyOfficeCallbackInterceptor\Service\HealthCheckService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

/**
 * Controller for settings API endpoints
 */
class SettingsController extends Controller {
    private ConfigService $configService;
    private HealthCheckService $healthCheckService;

    public function __construct(
        string $appName,
        IRequest $request,
        ConfigService $configService,
        HealthCheckService $healthCheckService
    ) {
        parent::__construct($appName, $request);
        $this->configService = $configService;
        $this->healthCheckService = $healthCheckService;
    }

    /**
     * Get current configuration
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    public function getConfig(): JSONResponse {
        try {
            $config = $this->configService->getAll();

            // Don't send sensitive data in plain text
            if (!empty($config['onlyoffice_secret'])) {
                $config['onlyoffice_secret'] = str_repeat('*', 8);
            }
            if (!empty($config['auth_token'])) {
                $config['auth_token'] = str_repeat('*', 8);
            }

            return new JSONResponse([
                'status' => 'success',
                'config' => $config,
            ]);
        } catch (\Exception $e) {
            return new JSONResponse([
                'status' => 'error',
                'message' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Save settings
     *
     * @NoAdminRequired
     */
    public function saveSettings(): JSONResponse {
        try {
            $data = $this->request->getParams();

            // Validate required fields
            if (isset($data['enabled']) && $data['enabled']) {
                if (empty($data['django_callback_url'])) {
                    return new JSONResponse([
                        'status' => 'error',
                        'message' => 'Django callback URL is required when interceptor is enabled',
                    ], 400);
                }
            }

            // Save configuration
            $this->configService->saveAll($data);

            // If health check is enabled and URL is provided, run it now
            if (isset($data['health_check_enabled']) && $data['health_check_enabled']
                && !empty($data['health_check_url'])) {
                $this->healthCheckService->check();
            }

            return new JSONResponse([
                'status' => 'success',
                'message' => 'Settings saved successfully',
            ]);

        } catch (\Exception $e) {
            $this->configService->error('Failed to save settings', [
                'error' => $e->getMessage(),
            ]);

            return new JSONResponse([
                'status' => 'error',
                'message' => 'Failed to save settings: ' . $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Test health check
     *
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    public function testHealthCheck(): JSONResponse {
        try {
            $result = $this->healthCheckService->check();

            return new JSONResponse([
                'status' => 'success',
                'health_check' => $result,
            ]);

        } catch (\Exception $e) {
            return new JSONResponse([
                'status' => 'error',
                'message' => 'Health check failed: ' . $e->getMessage(),
            ], 500);
        }
    }
}
