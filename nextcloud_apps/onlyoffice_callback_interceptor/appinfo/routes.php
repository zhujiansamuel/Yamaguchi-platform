<?php

return [
    'routes' => [
        [
            'name' => 'Settings#saveSettings',
            'url' => '/settings',
            'verb' => 'POST',
        ],
        [
            'name' => 'Settings#getConfig',
            'url' => '/settings',
            'verb' => 'GET',
        ],
        [
            'name' => 'Settings#testHealthCheck',
            'url' => '/health-check',
            'verb' => 'GET',
        ],
    ]
];
