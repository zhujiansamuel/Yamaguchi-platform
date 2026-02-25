<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Listener;

use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Util;

/**
 * Listener to inject JavaScript interceptor into pages
 */
class LoadScriptListener implements IEventListener {

    public function handle(Event $event): void {
        if (!($event instanceof BeforeTemplateRenderedEvent)) {
            return;
        }

        // Only load on non-public pages (logged in users)
        if ($event->isLoggedIn()) {
            Util::addScript('onlyoffice_callback_interceptor', 'interceptor');
            Util::addScript('onlyoffice_callback_interceptor', 'sidebar-info');
        }
    }
}
