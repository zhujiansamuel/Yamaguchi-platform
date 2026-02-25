<?php
script('onlyoffice_callback_interceptor', 'admin-settings');
style('onlyoffice_callback_interceptor', 'admin-settings');
?>

<div id="onlyoffice-callback-interceptor" class="section">
    <h2><?php p($l->t('OnlyOffice Callback Interceptor')); ?></h2>
    <p class="settings-hint">
        <?php p($l->t('Configure callback redirection to Django backend for OnlyOffice document editing.')); ?>
    </p>

    <div class="onlyoffice-settings-section">
        <h3><?php p($l->t('Basic Settings')); ?></h3>

        <p>
            <input type="checkbox" id="enabled" class="checkbox"
                   <?php if ($_['enabled']): ?>checked="checked"<?php endif; ?> />
            <label for="enabled"><?php p($l->t('Enable Callback Interceptor')); ?></label>
        </p>

        <p>
            <label for="django_callback_url"><?php p($l->t('Django Callback URL')); ?></label><br/>
            <input type="text" id="django_callback_url" name="django_callback_url"
                   value="<?php p($_['django_callback_url']); ?>"
                   placeholder="http://data.yamaguchi.lan/api/acquisition/onlyoffice/callback/"
                   style="width: 400px;" />
            <em><?php p($l->t('URL where OnlyOffice callbacks will be sent')); ?></em>
        </p>

        <p>
            <label for="path_filter"><?php p($l->t('Path Filter')); ?></label><br/>
            <input type="text" id="path_filter" name="path_filter"
                   value="<?php p($_['path_filter']); ?>"
                   placeholder="/Data/"
                   style="width: 400px;" />
            <em><?php p($l->t('Only intercept files in this path (leave empty for all files)')); ?></em>
        </p>
    </div>

    <div class="onlyoffice-settings-section">
        <h3><?php p($l->t('Security Settings')); ?></h3>

        <p>
            <label for="onlyoffice_secret"><?php p($l->t('OnlyOffice Secret (JWT)')); ?></label><br/>
            <input type="password" id="onlyoffice_secret" name="onlyoffice_secret"
                   value="<?php p($_['onlyoffice_secret']); ?>"
                   placeholder="Enter OnlyOffice secret key"
                   style="width: 400px;" />
            <em><?php p($l->t('Secret key for JWT token signing')); ?></em>
        </p>

        <p>
            <label for="auth_token"><?php p($l->t('Authentication Token')); ?></label><br/>
            <input type="password" id="auth_token" name="auth_token"
                   value="<?php p($_['auth_token']); ?>"
                   placeholder="Enter authentication token"
                   style="width: 400px;" />
            <em><?php p($l->t('Token to include in callback request headers (X-Auth-Token)')); ?></em>
        </p>
    </div>

    <div class="onlyoffice-settings-section">
        <h3><?php p($l->t('Metadata Settings')); ?></h3>

        <p>
            <input type="checkbox" id="include_user_metadata" class="checkbox"
                   <?php if ($_['include_user_metadata']): ?>checked="checked"<?php endif; ?> />
            <label for="include_user_metadata"><?php p($l->t('Include User Metadata')); ?></label>
            <em><?php p($l->t('Add user ID and display name to callback')); ?></em>
        </p>

        <p>
            <input type="checkbox" id="include_timestamp" class="checkbox"
                   <?php if ($_['include_timestamp']): ?>checked="checked"<?php endif; ?> />
            <label for="include_timestamp"><?php p($l->t('Include Timestamp')); ?></label>
            <em><?php p($l->t('Add edit start timestamp to callback')); ?></em>
        </p>
    </div>

    <div class="onlyoffice-settings-section">
        <h3><?php p($l->t('Health Check Settings')); ?></h3>

        <p>
            <input type="checkbox" id="health_check_enabled" class="checkbox"
                   <?php if ($_['health_check_enabled']): ?>checked="checked"<?php endif; ?> />
            <label for="health_check_enabled"><?php p($l->t('Enable Health Check')); ?></label>
            <em><?php p($l->t('Verify Django backend is healthy before intercepting callbacks')); ?></em>
        </p>

        <p>
            <label for="health_check_url"><?php p($l->t('Health Check URL')); ?></label><br/>
            <input type="text" id="health_check_url" name="health_check_url"
                   value="<?php p($_['health_check_url']); ?>"
                   placeholder="http://data.yamaguchi.lan/api/acquisition/health/"
                   style="width: 400px;" />
            <em><?php p($l->t('URL for Django health check endpoint')); ?></em>
        </p>

        <p>
            <label for="health_check_interval"><?php p($l->t('Health Check Interval (seconds)')); ?></label><br/>
            <input type="number" id="health_check_interval" name="health_check_interval"
                   value="<?php p($_['health_check_interval']); ?>"
                   min="60" max="3600"
                   style="width: 150px;" />
            <em><?php p($l->t('How often to check Django health')); ?></em>
        </p>

        <p>
            <button id="test-health-check" class="button"><?php p($l->t('Test Health Check Now')); ?></button>
            <span id="health-check-result"></span>
        </p>
    </div>

    <div class="onlyoffice-settings-section">
        <h3><?php p($l->t('Advanced Settings')); ?></h3>

        <p>
            <input type="checkbox" id="debug_mode" class="checkbox"
                   <?php if ($_['debug_mode']): ?>checked="checked"<?php endif; ?> />
            <label for="debug_mode"><?php p($l->t('Enable Debug Mode')); ?></label>
            <em><?php p($l->t('Log detailed information about callback interception')); ?></em>
        </p>
    </div>

    <p>
        <button id="save-settings" class="button-primary"><?php p($l->t('Save Settings')); ?></button>
        <span id="save-result"></span>
    </p>

    <div class="onlyoffice-info-section">
        <h3><?php p($l->t('How It Works')); ?></h3>
        <ol>
            <li><?php p($l->t('When a user opens a document in OnlyOffice, this app intercepts the configuration')); ?></li>
            <li><?php p($l->t('The callback URL is modified to point to your Django backend')); ?></li>
            <li><?php p($l->t('Django receives the callback, processes data, and forwards it to Nextcloud')); ?></li>
            <li><?php p($l->t('Nextcloud saves the file as usual, maintaining full functionality')); ?></li>
        </ol>

        <p><strong><?php p($l->t('Note:')); ?></strong>
            <?php p($l->t('Your Django backend must forward callbacks to Nextcloud to ensure files are saved properly.')); ?>
        </p>
    </div>
</div>
