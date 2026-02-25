<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Service;

use OCP\IConfig;
use Psr\Log\LoggerInterface;

/**
 * Service for managing plugin configuration
 */
class ConfigService {
    private IConfig $config;
    private LoggerInterface $logger;
    private string $appName = 'onlyoffice_callback_interceptor';

    // Default configuration values
    private const DEFAULTS = [
        'enabled' => false,
        'django_callback_url' => '',
        'onlyoffice_secret' => '',
        'auth_token' => '',
        'path_filter' => '/Data/',
        'debug_mode' => false,
        'health_check_enabled' => true,
        'health_check_url' => '',
        'health_check_interval' => 300,
        'include_user_metadata' => true,
        'include_timestamp' => true,
        'last_health_check' => 0,
        'backend_healthy' => true,
    ];

    // Additional path filters for tracking tasks
    // These paths will be monitored in addition to the primary path_filter
    // Format: 'folder_name' => 'filename_prefix'
    private const TRACKING_PATH_FILTERS = [
        'official_website_redirect_to_yamato_tracking' => 'OWRYT-',
        'yamato_tracking_10' => 'YT10-',
        'yamato_tracking' => 'YTO-',
        'yamato_tracking_only' => 'YTO-',
        'japan_post_tracking_only' => 'JPTO-',
        'japan_post_tracking' => 'JPTO-',
        'japan_post_tracking_10' => 'JPT10-',
    ];

    public function __construct(IConfig $config, LoggerInterface $logger) {
        $this->config = $config;
        $this->logger = $logger;
    }

    /**
     * Get a configuration value
     */
    public function get(string $key, $default = null) {
        $defaultValue = $default ?? (self::DEFAULTS[$key] ?? null);
        return $this->config->getAppValue($this->appName, $key, $defaultValue);
    }

    /**
     * Set a configuration value
     */
    public function set(string $key, $value): void {
        $this->config->setAppValue($this->appName, $key, $value);
    }

    /**
     * Get all configuration values
     */
    public function getAll(): array {
        $config = [];
        foreach (self::DEFAULTS as $key => $default) {
            $config[$key] = $this->get($key);
        }
        return $config;
    }

    /**
     * Save multiple configuration values
     */
    public function saveAll(array $values): void {
        foreach ($values as $key => $value) {
            if (array_key_exists($key, self::DEFAULTS)) {
                // Convert boolean values
                if (is_bool(self::DEFAULTS[$key])) {
                    $value = $value ? 'true' : 'false';
                }
                $this->set($key, $value);
            }
        }

        if ($this->isDebugMode()) {
            $this->logger->info('Configuration saved', ['app' => $this->appName]);
        }
    }

    /**
     * Check if interceptor is enabled
     */
    public function isEnabled(): bool {
        return $this->toBool($this->get('enabled'));
    }

    /**
     * Check if debug mode is enabled
     */
    public function isDebugMode(): bool {
        return $this->toBool($this->get('debug_mode'));
    }

    /**
     * Check if health check is enabled
     */
    public function isHealthCheckEnabled(): bool {
        return $this->toBool($this->get('health_check_enabled'));
    }

    /**
     * Check if backend is healthy
     */
    public function isBackendHealthy(): bool {
        return $this->toBool($this->get('backend_healthy'));
    }

    /**
     * Set backend health status
     */
    public function setBackendHealthy(bool $healthy): void {
        $this->set('backend_healthy', $healthy ? 'true' : 'false');
        $this->set('last_health_check', (string)time());
    }

    /**
     * Check if health check should run (based on interval)
     */
    public function shouldRunHealthCheck(): bool {
        if (!$this->isHealthCheckEnabled()) {
            return false;
        }

        $lastCheck = (int)$this->get('last_health_check');
        $interval = (int)$this->get('health_check_interval');
        return (time() - $lastCheck) >= $interval;
    }

    /**
     * Get Django callback URL
     */
    public function getDjangoCallbackUrl(): string {
        return $this->get('django_callback_url');
    }

    /**
     * Get OnlyOffice secret (JWT)
     */
    public function getOnlyOfficeSecret(): string {
        return $this->get('onlyoffice_secret');
    }

    /**
     * Get authentication token
     */
    public function getAuthToken(): string {
        return $this->get('auth_token');
    }

    /**
     * Get path filter
     */
    public function getPathFilter(): string {
        return $this->get('path_filter');
    }

    /**
     * Check if user metadata should be included
     */
    public function shouldIncludeUserMetadata(): bool {
        return $this->toBool($this->get('include_user_metadata'));
    }

    /**
     * Check if timestamp should be included
     */
    public function shouldIncludeTimestamp(): bool {
        return $this->toBool($this->get('include_timestamp'));
    }

    /**
     * Check if a file path matches the configured filter
     */
    public function matchesPathFilter(string $filePath): bool {
        $filter = $this->getPathFilter();

        // Normalize path: Nextcloud sometimes includes user prefix like /admin/files/data_platform/
        // We want to match against the relative path from the user's files root
        $normalizedPath = $filePath;
        if (preg_match('/^\/[^\/]+\/files(\/.*)$/', $filePath, $matches)) {
            $normalizedPath = $matches[1];
        }

        $cleanPath = '/' . trim($normalizedPath, '/') . '/';

        // Check if matches primary filter (e.g., /data_platform/)
        if (!empty($filter)) {
            // Ensure filter has leading/trailing slashes for consistent matching
            $cleanFilter = '/' . trim($filter, '/') . '/';
            
            if (strpos($cleanPath, $cleanFilter) === 0) {
                return true;
            }
        }

        // Check if matches any tracking path filter
        foreach (self::TRACKING_PATH_FILTERS as $trackingPath => $filenamePrefix) {
            $cleanTrackingFilter = '/' . trim($trackingPath, '/') . '/';
            if (strpos($cleanPath, $cleanTrackingFilter) !== false) {
                return true;
            }
        }

        // If no filter is configured, default to true (allow all)
        return empty($filter);
    }

    /**
     * Get the filename prefix for a given tracking path
     * Returns null if the path doesn't match any tracking configuration
     */
    public function getTrackingFilenamePrefix(string $filePath): ?string {
        // Normalize path
        $normalizedPath = $filePath;
        if (preg_match('/^\/[^\/]+\/files(\/.*)$/', $filePath, $matches)) {
            $normalizedPath = $matches[1];
        }

        $cleanPath = '/' . trim($normalizedPath, '/') . '/';

        foreach (self::TRACKING_PATH_FILTERS as $trackingPath => $filenamePrefix) {
            $cleanTrackingFilter = '/' . trim($trackingPath, '/') . '/';
            if (strpos($cleanPath, $cleanTrackingFilter) !== false) {
                return $filenamePrefix;
            }
        }

        return null;
    }

    /**
     * Get all tracking path filters
     */
    public function getTrackingPathFilters(): array {
        return self::TRACKING_PATH_FILTERS;
    }

    /**
     * Log a debug message
     */
    public function debug(string $message, array $context = []): void {
        if ($this->isDebugMode()) {
            $context['app'] = $this->appName;
            $this->logger->info($message, $context);
        }
    }

    /**
     * Log an error message
     */
    public function error(string $message, array $context = []): void {
        $context['app'] = $this->appName;
        $this->logger->error($message, $context);
    }

    /**
     * Normalize boolean-like configuration values.
     */
    private function toBool($value): bool {
        return $value === true
            || $value === 'true'
            || $value === '1'
            || $value === 'yes'
            || $value === 1;
    }
}
