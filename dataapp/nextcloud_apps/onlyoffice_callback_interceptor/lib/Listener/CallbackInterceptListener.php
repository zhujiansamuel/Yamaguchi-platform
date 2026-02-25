<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Listener;

use OCA\OnlyOfficeCallbackInterceptor\Service\ConfigService;
use OCA\OnlyOfficeCallbackInterceptor\Service\NotificationService;
use OCP\AppFramework\Http\Events\BeforeControllerEvent;
use OCP\EventDispatcher\IEventListener;
use Symfony\Contracts\EventDispatcher\Event;
use OCP\IRequest;
use OCP\IUserSession;

/**
 * Listener for OnlyOffice callback requests
 * Intercepts /apps/onlyoffice/track POST requests
 */
class CallbackInterceptListener implements IEventListener {
    private ConfigService $configService;
    private NotificationService $notificationService;
    private IRequest $request;
    private IUserSession $userSession;

    public function __construct(
        ConfigService $configService,
        NotificationService $notificationService,
        IRequest $request,
        IUserSession $userSession
    ) {
        $this->configService = $configService;
        $this->notificationService = $notificationService;
        $this->request = $request;
        $this->userSession = $userSession;
    }

    public function handle(object $event): void {
        $controllerClass = null;
        $method = null;

        if ($event instanceof BeforeControllerEvent) {
            $controller = $event->getController();
            // In Nextcloud 32, getController might return an array [controller, method]
            if (is_array($controller)) {
                $controllerClass = is_object($controller[0]) ? get_class($controller[0]) : null;
            } else {
                $controllerClass = is_object($controller) ? get_class($controller) : null;
            }
            $method = $event->getMethod();
        }

        $requestUri = $this->request->getRequestUri();

        // Use debug method if it exists, otherwise ignore
        if (method_exists($this->configService, 'debug')) {
            $this->configService->debug('[Callback] Listener triggered', [
                'event_class' => get_class($event),
                'controller' => $controllerClass,
                'method' => $method,
                'request_uri' => $requestUri,
                'http_method' => $this->request->getMethod(),
            ]);
        }

        // Check if this is an OnlyOffice track callback
        $isTrackController = $controllerClass && strpos($controllerClass, 'OCA\\Onlyoffice\\Controller\\CallbackController') !== false && $method === 'track';
        $isTrackUri = strpos($requestUri, '/apps/onlyoffice/track') !== false;

        if (!$isTrackController && !$isTrackUri) {
            return;
        }

        if (!$this->configService->isEnabled()) {
            $this->configService->debug('[Callback] Interceptor is disabled');
            return;
        }

        // Collect parameters
        $params = $this->request->getParams() ?? [];

        // Try to parse JSON body if not parsed yet
        if (empty($params) && method_exists($this->request, 'getContent')) {
            $raw = $this->request->getContent();
            if (!empty($raw)) {
                $decoded = json_decode($raw, true);
                if (is_array($decoded)) {
                    $params = $decoded;
                }
            }
        }

        // Attempt to decode doc token if present and no file path found
        $docToken = $this->request->getParam('doc');
        $fileInfoFromDoc = [];
        if (!empty($docToken)) {
            $fileInfoFromDoc = $this->decodeDocToken($docToken) ?? [];
        }

        $filePath = $params['filePath'] ?? $params['path'] ?? ($fileInfoFromDoc['filePath'] ?? '');

        if (!empty($filePath) && !$this->configService->matchesPathFilter($filePath)) {
            $this->configService->debug('[Callback] File does not match path filter', [
                'file_path' => $filePath,
                'filter' => $this->configService->getPathFilter(),
            ]);
            return;
        }

        $metadata = [
            'event_type' => 'onlyoffice_track',
            'file_path' => $filePath,
            'url' => $params['url'] ?? null,
            'key' => $params['key'] ?? null,
            'status' => $params['status'] ?? null,
            'callback_time' => date('c'),
            'users' => $params['users'] ?? null,
            'actions' => $params['actions'] ?? null,
            'doc_token_present' => !empty($docToken),
            'file_id' => $fileInfoFromDoc['fileId'] ?? null,
            'owner_id' => $fileInfoFromDoc['ownerId'] ?? null,
            'user_id_from_doc' => $fileInfoFromDoc['userId'] ?? null,
        ];

        // Attach doc token raw for debugging (do not forward secret keys)
        if (!empty($docToken)) {
            $metadata['doc_token'] = $docToken;
        }

        // Add session user info if available
        $user = $this->userSession->getUser();
        if ($user !== null) {
            $metadata['session_user_id'] = $user->getUID();
            $metadata['session_user_display_name'] = $user->getDisplayName();
        }

        $this->configService->debug('[Callback] Sending notification to Django', [
            'metadata' => $metadata,
        ]);

        $this->notificationService->notifyDjango($metadata);
    }

    /**
     * Decode the doc JWT token to get file information
     */
    private function decodeDocToken(string $token): ?array {
        try {
            // JWT tokens are in format: header.payload.signature
            $parts = explode('.', $token);
            if (count($parts) !== 3) {
                return null;
            }

            // Decode the payload (second part)
            $payload = base64_decode(strtr($parts[1], '-_', '+/'));
            $data = json_decode($payload, true);

            return $data;
        } catch (\Exception $e) {
            $this->configService->error('Failed to decode JWT token', [
                'error' => $e->getMessage(),
            ]);
            return null;
        }
    }
}
