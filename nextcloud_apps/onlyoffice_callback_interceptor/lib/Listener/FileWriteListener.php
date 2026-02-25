<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Listener;

use OCA\OnlyOfficeCallbackInterceptor\Service\ConfigService;
use OCA\OnlyOfficeCallbackInterceptor\Service\NotificationService;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeWrittenEvent;
use OCP\Files\File;
use OCP\IRequest;
use OCP\IUserSession;

/**
 * Listener for file write events
 * Detects OnlyOffice saves and notifies Django
 */
class FileWriteListener implements IEventListener {
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

    public function handle(Event $event): void {
        // STEP 1: Log that listener was triggered
        $this->configService->debug('[STEP 1] FileWriteListener triggered', [
            'event_class' => get_class($event)
        ]);

        // Accept multiple event types
        if (!($event instanceof \OCP\Files\Events\Node\AbstractNodeEvent)) {
            $this->configService->debug('[STEP 1 FAILED] Event is not a file event', [
                'event_class' => get_class($event)
            ]);
            return;
        }

        $this->configService->debug('[STEP 2] Event is a file event', [
            'event_type' => get_class($event)
        ]);

        // Check if interceptor is enabled
        if (!$this->configService->isEnabled()) {
            $this->configService->debug('[STEP 2 FAILED] Interceptor is disabled');
            return;
        }

        $this->configService->debug('[STEP 3] Interceptor is enabled');

        $node = $event->getNode();

        // Only handle files (not folders)
        if (!($node instanceof File)) {
            $this->configService->debug('[STEP 3 FAILED] Node is not a file, it is a folder');
            return;
        }

        $this->configService->debug('[STEP 4] Node is a file');

        // Get file path
        $filePath = $node->getPath();

        $this->configService->debug('[STEP 5] Got file path', [
            'file_path' => $filePath,
            'file_id' => $node->getId(),
        ]);

        // Check if file matches path filter
        if (!$this->configService->matchesPathFilter($filePath)) {
            $this->configService->debug('[STEP 5 FAILED] File does not match path filter', [
                'file_path' => $filePath,
                'filter' => $this->configService->getPathFilter(),
            ]);
            return;
        }

        $this->configService->debug('[STEP 6] File matches path filter');

        // Log request context
        $this->configService->debug('[STEP 7] Checking request context', [
            'user_agent' => $this->request->getHeader('User-Agent'),
            'request_uri' => $this->request->getRequestUri(),
            'referer' => $this->request->getHeader('Referer'),
        ]);

        // Check if this is an OnlyOffice save
        if (!$this->isOnlyOfficeSave()) {
            $this->configService->debug('[STEP 7 FAILED] Not an OnlyOffice save', [
                'file_path' => $filePath,
                'user_agent' => $this->request->getHeader('User-Agent'),
            ]);
            return;
        }

        $this->configService->debug('[STEP 8] OnlyOffice file save detected!', [
            'file_path' => $filePath,
            'file_id' => $node->getId(),
        ]);

        // Collect metadata
        $metadata = $this->collectMetadata($node);

        $this->configService->debug('[STEP 9] Sending notification to Django', [
            'metadata' => $metadata,
        ]);

        // Send notification to Django
        $this->notificationService->notifyDjango($metadata);

        $this->configService->debug('[STEP 10] Notification sent to Django');
    }

    /**
     * Check if this is an OnlyOffice save operation
     */
    private function isOnlyOfficeSave(): bool {
        // Check User-Agent header
        $userAgent = $this->request->getHeader('User-Agent');
        if (strpos($userAgent, 'Node.js') !== false) {
            // OnlyOffice uses Node.js for callbacks
            return true;
        }

        // Check if request is from OnlyOffice callback
        $requestUri = $this->request->getRequestUri();
        if (strpos($requestUri, '/apps/onlyoffice/track') !== false) {
            return true;
        }

        // Check referer
        $referer = $this->request->getHeader('Referer');
        if (strpos($referer, 'onlyoffice') !== false) {
            return true;
        }

        return false;
    }

    /**
     * Collect file and user metadata
     */
    private function collectMetadata(File $node): array {
        $metadata = [
            'event_type' => 'file_updated',
            'file_path' => $node->getPath(),
            'file_id' => $node->getId(),
            'file_name' => $node->getName(),
            'file_size' => $node->getSize(),
            'mime_type' => $node->getMimeType(),
            'modified_time' => date('c', $node->getMTime()),
        ];

        // Add user metadata if enabled
        if ($this->configService->shouldIncludeUserMetadata()) {
            $user = $this->userSession->getUser();
            if ($user !== null) {
                $metadata['user_id'] = $user->getUID();
                $metadata['user_display_name'] = $user->getDisplayName();
            }
        }

        // Add timestamp if enabled
        if ($this->configService->shouldIncludeTimestamp()) {
            $metadata['event_timestamp'] = date('c');
        }

        return $metadata;
    }
}
