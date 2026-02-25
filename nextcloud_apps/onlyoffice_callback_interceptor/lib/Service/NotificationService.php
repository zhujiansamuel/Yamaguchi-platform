<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Service;

use OCP\Http\Client\IClientService;
use Psr\Log\LoggerInterface;

/**
 * Service for sending notifications to Django backend
 */
class NotificationService {
    private IClientService $clientService;
    private ConfigService $configService;
    private LoggerInterface $logger;

    public function __construct(
        IClientService $clientService,
        ConfigService $configService,
        LoggerInterface $logger
    ) {
        $this->clientService = $clientService;
        $this->configService = $configService;
        $this->logger = $logger;
    }

    /**
     * Send file update notification to Django
     */
    public function notifyDjango(array $metadata): void {
        $notificationUrl = $this->configService->getDjangoCallbackUrl();

        if (empty($notificationUrl)) {
            $this->logger->error('Django notification URL not configured');
            return;
        }

        try {
            $client = $this->clientService->newClient();

            // Prepare request headers
            $headers = [
                'Content-Type' => 'application/json',
            ];

            // Add auth token if configured
            $authToken = $this->configService->getAuthToken();
            if (!empty($authToken)) {
                $headers['X-Auth-Token'] = $authToken;
            }

            // Add source identifier
            $headers['X-Source'] = 'nextcloud-onlyoffice-interceptor';

            // Append file_path (and key/user if available) as query params so Django can parse via GET
            $queryParams = [];
            if (!empty($metadata['file_path'])) {
                $queryParams['file_path'] = $metadata['file_path'];
            }
            if (!empty($metadata['key'])) {
                $queryParams['key'] = $metadata['key'];
            }

            // Prefer explicit user_id, then session_user_id, then doc token user_id
            $userId = $metadata['user_id'] ?? $metadata['session_user_id'] ?? $metadata['user_id_from_doc'] ?? null;
            if (!empty($userId)) {
                $queryParams['user_id'] = $userId;
            }
            if (!empty($metadata['owner_id'] ?? null)) {
                $queryParams['owner_id'] = $metadata['owner_id'];
            }
            if (!empty($metadata['user_display_name'] ?? null)) {
                $queryParams['user_display_name'] = $metadata['user_display_name'];
            }
            if (!empty($metadata['session_user_display_name'] ?? null)) {
                $queryParams['session_user_display_name'] = $metadata['session_user_display_name'];
            }

            $url = $notificationUrl;
            if (!empty($queryParams)) {
                $separator = strpos($url, '?') !== false ? '&' : '?';
                $url .= $separator . http_build_query($queryParams);
            }

            // Send notification
            $response = $client->post($url, [
                'headers' => $headers,
                'json' => $metadata,
                'timeout' => 10,
                'connect_timeout' => 5,
            ]);

            $statusCode = $response->getStatusCode();

            if ($statusCode >= 200 && $statusCode < 300) {
                $this->logger->debug('Successfully notified Django', [
                    'url' => $notificationUrl,
                    'file_path' => $metadata['file_path'] ?? 'unknown',
                    'status' => $statusCode,
                ]);
            } else {
                $this->logger->error('Django notification failed', [
                    'url' => $notificationUrl,
                    'status' => $statusCode,
                    'file_path' => $metadata['file_path'] ?? 'unknown',
                ]);
            }

        } catch (\Exception $e) {
            $this->logger->error('Failed to notify Django', [
                'url' => $notificationUrl,
                'error' => $e->getMessage(),
                'file_path' => $metadata['file_path'] ?? 'unknown',
            ]);
        }
    }
}
