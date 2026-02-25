<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Service;

use OCP\Http\Client\IClientService;
use Psr\Log\LoggerInterface;

/**
 * Service for checking Django backend health
 */
class HealthCheckService {
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
     * Perform health check on Django backend
     */
    public function check(): array {
        $healthCheckUrl = $this->configService->get('health_check_url');

        if (empty($healthCheckUrl)) {
            return [
                'healthy' => false,
                'message' => 'Health check URL not configured',
                'status_code' => null,
            ];
        }

        try {
            $client = $this->clientService->newClient();
            $response = $client->get($healthCheckUrl, [
                'timeout' => 5,
                'connect_timeout' => 3,
            ]);

            $statusCode = $response->getStatusCode();
            $healthy = $statusCode >= 200 && $statusCode < 300;

            $result = [
                'healthy' => $healthy,
                'message' => $healthy ? 'Django backend is healthy' : "Health check returned status $statusCode",
                'status_code' => $statusCode,
            ];

            // Try to parse response body
            try {
                $body = json_decode($response->getBody(), true);
                if (is_array($body)) {
                    $result['response'] = $body;
                }
            } catch (\Exception $e) {
                // Ignore JSON parsing errors
            }

            // Update backend health status
            $this->configService->setBackendHealthy($healthy);

            if ($this->configService->isDebugMode()) {
                $this->logger->info('Health check completed', [
                    'app' => 'onlyoffice_callback_interceptor',
                    'healthy' => $healthy,
                    'url' => $healthCheckUrl,
                    'status' => $statusCode,
                ]);
            }

            return $result;

        } catch (\Exception $e) {
            $result = [
                'healthy' => false,
                'message' => 'Health check failed: ' . $e->getMessage(),
                'status_code' => null,
                'error' => $e->getMessage(),
            ];

            // Update backend health status
            $this->configService->setBackendHealthy(false);

            $this->logger->error('Health check failed', [
                'app' => 'onlyoffice_callback_interceptor',
                'url' => $healthCheckUrl,
                'error' => $e->getMessage(),
            ]);

            return $result;
        }
    }

    /**
     * Check health if needed (based on interval) and return cached status
     */
    public function checkIfNeeded(): bool {
        if (!$this->configService->isHealthCheckEnabled()) {
            return true; // If health check is disabled, assume healthy
        }

        if ($this->configService->shouldRunHealthCheck()) {
            $result = $this->check();
            return $result['healthy'];
        }

        // Return cached health status
        return $this->configService->isBackendHealthy();
    }
}
