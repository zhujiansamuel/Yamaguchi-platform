<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Listener;

use OCA\OnlyOfficeCallbackInterceptor\Service\ConfigService;
use OCA\OnlyOfficeCallbackInterceptor\Service\HealthCheckService;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\IUserSession;
use Firebase\JWT\JWT;

/**
 * Listener for OnlyOffice configuration events
 * This intercepts the OnlyOffice editor config and modifies the callback URL
 */
class OnlyOfficeConfigListener implements IEventListener {
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

    public function handle(Event $event): void {
        // Check if interceptor is enabled
        if (!$this->configService->isEnabled()) {
            $this->configService->debug('Interceptor is disabled, skipping');
            return;
        }

        // Check backend health
        if ($this->configService->isHealthCheckEnabled()) {
            $healthy = $this->healthCheckService->checkIfNeeded();
            if (!$healthy) {
                $this->configService->debug('Backend is unhealthy, skipping interception');
                return;
            }
        }

        $this->configService->debug('OnlyOffice config event triggered', [
            'event_class' => get_class($event),
        ]);

        // Try to extract OnlyOffice config from the event
        // The exact method depends on the richdocuments app version
        $config = $this->extractConfigFromEvent($event);

        if ($config !== null) {
            $this->modifyConfig($config, $event);
        }
    }

    /**
     * Extract OnlyOffice config from event
     * This method tries different approaches to get the config
     */
    private function extractConfigFromEvent(Event $event): ?array {
        // Try to get config from event methods
        if (method_exists($event, 'getConfig')) {
            return $event->getConfig();
        }

        if (method_exists($event, 'getArgument')) {
            try {
                return $event->getArgument('config');
            } catch (\Exception $e) {
                // Argument doesn't exist
            }
        }

        // If we can't extract config, we'll use a different approach
        // We'll hook into the HTTP response modification instead
        return null;
    }

    /**
     * Modify OnlyOffice configuration to redirect callbacks
     */
    private function modifyConfig(?array &$config, Event $event): void {
        if ($config === null) {
            return;
        }

        // Get file path from config
        $filePath = $config['document']['fileType'] ?? '';
        $documentKey = $config['document']['key'] ?? '';

        // Check if file matches path filter
        if (!empty($filePath) && !$this->configService->matchesPathFilter($filePath)) {
            $this->configService->debug('File path does not match filter', [
                'file_path' => $filePath,
                'filter' => $this->configService->getPathFilter(),
            ]);
            return;
        }

        // Get original callback URL
        $originalCallback = $config['editorConfig']['callbackUrl'] ?? '';

        if (empty($originalCallback)) {
            $this->configService->debug('No callback URL found in config');
            return;
        }

        // Build new callback URL with parameters
        $djangoUrl = $this->buildDjangoCallbackUrl($originalCallback, $filePath);

        // Replace callback URL
        $config['editorConfig']['callbackUrl'] = $djangoUrl;

        // Add JWT token if OnlyOffice secret is configured
        $secret = $this->configService->getOnlyOfficeSecret();
        if (!empty($secret)) {
            try {
                $config['token'] = $this->generateJWT($config, $secret);
            } catch (\Exception $e) {
                $this->configService->error('Failed to generate JWT token', [
                    'error' => $e->getMessage(),
                ]);
            }
        }

        $this->configService->debug('Callback URL modified', [
            'original' => $originalCallback,
            'new' => $djangoUrl,
            'file_path' => $filePath,
        ]);
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
