<?php

declare(strict_types=1);

namespace OCA\OnlyOfficeCallbackInterceptor\Settings;

use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\Settings\IIconSection;

/**
 * Admin section for OnlyOffice Callback Interceptor settings
 */
class AdminSection implements IIconSection {
    private IL10N $l;
    private IURLGenerator $urlGenerator;

    public function __construct(IL10N $l, IURLGenerator $urlGenerator) {
        $this->l = $l;
        $this->urlGenerator = $urlGenerator;
    }

    /**
     * @return string ID of the section
     */
    public function getID(): string {
        return 'onlyoffice-callback';
    }

    /**
     * @return string Name of the section
     */
    public function getName(): string {
        return $this->l->t('OnlyOffice Callback');
    }

    /**
     * @return int Priority (lower number = higher in the list)
     */
    public function getPriority(): int {
        return 75;
    }

    /**
     * @return string Icon for the section
     */
    public function getIcon(): string {
        // Use a default Nextcloud icon
        return $this->urlGenerator->imagePath('core', 'actions/settings-dark.svg');
    }
}
