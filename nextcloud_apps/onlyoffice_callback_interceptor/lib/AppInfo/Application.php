<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\AppInfo;

use OCA\OnlyOfficeCallbackInterceptor\Listener\FileWriteListener;
use OCA\OnlyOfficeCallbackInterceptor\Listener\CallbackInterceptListener;
use OCA\OnlyOfficeCallbackInterceptor\Middleware\CallbackInterceptorMiddleware;
use OCA\OnlyOfficeCallbackInterceptor\Middleware\TrackCallbackMiddleware;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\AppFramework\Http\Events\BeforeControllerEvent;
use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCP\Files\Events\Node\NodeWrittenEvent;
use OCA\OnlyOfficeCallbackInterceptor\Listener\LoadScriptListener;

/**
 * Main application class for OnlyOffice Callback Interceptor
 */
class Application extends App implements IBootstrap {
    public const APP_ID = 'onlyoffice_callback_interceptor';

    public function __construct(array $urlParams = []) {
        parent::__construct(self::APP_ID, $urlParams);
    }

    public function register(IRegistrationContext $context): void {
        // Register listener for file write events
        // This will detect OnlyOffice saves and notify Django

        // Register for multiple file events to ensure we catch the save
        $context->registerEventListener(
            NodeWrittenEvent::class,
            FileWriteListener::class
        );

        // Also try NodeCreatedEvent in case the file is being created
        $context->registerEventListener(
            \OCP\Files\Events\Node\NodeCreatedEvent::class,
            FileWriteListener::class
        );

        // And BeforeNodeWrittenEvent to catch before the write
        $context->registerEventListener(
            \OCP\Files\Events\Node\BeforeNodeWrittenEvent::class,
            FileWriteListener::class
        );

        // Register event listener for OnlyOffice track endpoint
        $context->registerEventListener(
            BeforeControllerEvent::class,
            CallbackInterceptListener::class
        );

        // Register listener to inject scripts (replaces app.php)
        $context->registerEventListener(
            BeforeTemplateRenderedEvent::class,
            LoadScriptListener::class
        );

        // Register middlewares for config interception and track interception
        $context->registerMiddleware(CallbackInterceptorMiddleware::class);
        $context->registerMiddleware(TrackCallbackMiddleware::class);
    }

    public function boot(IBootContext $context): void {
        // Log that the application has booted
        $logger = $context->getServerContainer()->get(\Psr\Log\LoggerInterface::class);
        $logger->info('[OnlyOffice Callback Interceptor] Application booted and event listeners registered', [
            'app' => self::APP_ID
        ]);

        // Early request sniffing for OnlyOffice track endpoint (best-effort)
        $container = $context->getServerContainer();
        $request = $container->get(\OCP\IRequest::class);
        $requestUri = $request->getRequestUri();

        if (strpos($requestUri, '/apps/onlyoffice/track') !== false) {
            $logger->info('[OnlyOffice Callback Interceptor] OnlyOffice track request detected in boot', [
                'uri' => $requestUri,
            ]);

            $listener = $container->get(CallbackInterceptListener::class);
            // In Nextcloud 32, GenericEvent is from Symfony
            if (class_exists('\Symfony\Component\EventDispatcher\GenericEvent')) {
                $listener->handle(new \Symfony\Component\EventDispatcher\GenericEvent());
            } else {
                $listener->handle(new \OCP\EventDispatcher\GenericEvent());
            }
        }
    }
}
