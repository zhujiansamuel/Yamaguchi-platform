<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Middleware;

use OCA\OnlyOfficeCallbackInterceptor\Service\ConfigService;
use OCA\OnlyOfficeCallbackInterceptor\Service\HealthCheckService;
use OCP\AppFramework\Http\JSONResponse;
use OCP\AppFramework\Middleware;
use OCP\IUserSession;
use Firebase\JWT\JWT;

/**
 * Middleware to intercept OnlyOffice config responses and modify callback URL
 */
class CallbackInterceptorMiddleware extends Middleware {
    private ConfigService $configService;
    private HealthCheckService $healthCheckService;
    private IUserSession $userSession;

    public function __construct(
        ConfigService $configService,
        HealthCheckService $healthCheckService,
        IUserSession $userSession
    ) {
        $this->configService = $configService;
        $this->healthCheckService = $healthCheckService;
        $this->userSession = $userSession;
    }

    /**
     * Modify the response after controller execution
     */
    public function afterController($controller, $methodName, $response) {
        // Check if this is an OnlyOffice config response
        if (!$this->shouldIntercept($controller, $methodName)) {
            return $response;
        }

        // Check if interceptor is enabled
        if (!$this->configService->isEnabled()) {
            $this->configService->debug('Interceptor is disabled, skipping');
            return $response;
        }

        // Check backend health
        if ($this->configService->isHealthCheckEnabled()) {
            $healthy = $this->healthCheckService->checkIfNeeded();
            if (!$healthy) {
                $this->configService->debug('Backend is unhealthy, skipping interception');
                return $response;
            }
        }

        // Modify the response
        return $this->modifyResponse($response);
    }

    /**
     * Check if we should intercept this controller/method
     */
    private function shouldIntercept($controller, string $methodName): bool {
        $controllerClass = get_class($controller);

        // Intercept OnlyOffice EditorApiController::config method
        if (strpos($controllerClass, 'OCA\Onlyoffice\Controller\EditorApiController') !== false
            && $methodName === 'config') {
            return true;
        }

        return false;
    }

    /**
     * Modify the response to change callback URL
     */
    private function modifyResponse($response) {
        if (!($response instanceof JSONResponse)) {
            return $response;
        }

        $data = $response->getData();

        // Check if this has the expected structure
        if (!isset($data['editorConfig']['callbackUrl'])) {
            $this->configService->debug('No callbackUrl found in response');
            return $response;
        }

        $originalCallback = $data['editorConfig']['callbackUrl'];

        // Get file path if available
        $filePath = $data['document']['url'] ?? '';
        if (isset($data['document']['key'])) {
            // Try to extract file path from key or other fields
            $filePath = $data['file']['path'] ?? $data['document']['title'] ?? '';
        }

        // Check if file matches path filter
        if (!empty($filePath) && !$this->configService->matchesPathFilter($filePath)) {
            $this->configService->debug('File path does not match filter', [
                'file_path' => $filePath,
                'filter' => $this->configService->getPathFilter(),
            ]);
            return $response;
        }

        // Build new callback URL
        $newCallback = $this->buildDjangoCallbackUrl($originalCallback, $filePath);

        // Update the callback URL
        $data['editorConfig']['callbackUrl'] = $newCallback;

        // Re-sign JWT token if needed
        $secret = $this->configService->getOnlyOfficeSecret();
        if (!empty($secret) && isset($data['token'])) {
            try {
                $data['token'] = $this->generateJWT($data, $secret);
            } catch (\Exception $e) {
                $this->configService->error('Failed to generate JWT token', [
                    'error' => $e->getMessage(),
                ]);
            }
        }

        $this->configService->debug('Callback URL modified', [
            'original' => $originalCallback,
            'new' => $newCallback,
            'file_path' => $filePath,
        ]);

        // Update response data
        $response->setData($data);

        return $response;
    }

    /**
     * Build Django callback URL with metadata parameters
     */
    private function buildDjangoCallbackUrl(string $originalCallback, string $filePath): string {
        $djangoUrl = $this->configService->getDjangoCallbackUrl();

        // Build query parameters
        $params = [
            'nextcloud_callback' => $originalCallback,
        ];

        // Add file path
        if (!empty($filePath)) {
            $params['file_path'] = $filePath;
        }

        // Add user metadata if enabled
        if ($this->configService->shouldIncludeUserMetadata()) {
            $user = $this->userSession->getUser();
            if ($user !== null) {
                $params['user_id'] = $user->getUID();
                $params['user_display_name'] = $user->getDisplayName();
            }
        }

        // Add timestamp if enabled
        if ($this->configService->shouldIncludeTimestamp()) {
            $params['edit_start_time'] = date('c'); // ISO 8601 format
        }

        // Build URL with query parameters
        $queryString = http_build_query($params);
        $separator = strpos($djangoUrl, '?') !== false ? '&' : '?';

        return $djangoUrl . $separator . $queryString;
    }

    /**
     * Generate JWT token for OnlyOffice
     */
    private function generateJWT(array $payload, string $secret): string {
        // OnlyOffice expects HS256 algorithm
        return JWT::encode($payload, $secret, 'HS256');
    }
}
