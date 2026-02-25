# OnlyOffice Callback Interceptor

Nextcloud app that intercepts OnlyOffice document editing callbacks and redirects them to a Django backend server for dual-callback architecture.

## Features

- ✅ **Automatic Callback URL Modification**: Redirects OnlyOffice callbacks to Django endpoint
- ✅ **JWT Token Signing**: Secure callbacks with OnlyOffice secret
- ✅ **Path-based Filtering**: Only intercept files in specific directories (e.g., `/Data/`)
- ✅ **User Metadata Injection**: Include user ID and display name in callbacks
- ✅ **Timestamp Tracking**: Add edit start timestamps to callbacks
- ✅ **Health Check**: Verify Django backend availability before interception
- ✅ **Automatic Fallback**: Disable interception if Django is unhealthy
- ✅ **Detailed Logging**: Debug mode for troubleshooting
- ✅ **Admin Configuration UI**: Easy setup through Nextcloud admin panel

## Architecture

```
User opens document in OnlyOffice
         ↓
Nextcloud intercepts configuration (this app)
         ↓
Callback URL modified to Django
         ↓
OnlyOffice sends callback to Django
         ↓
Django processes data and forwards to Nextcloud
         ↓
Nextcloud saves file (normal flow)
```

## Requirements

- Nextcloud 25.0 or higher
- PHP 7.4 or higher
- OnlyOffice integration app (`richdocuments`)
- Django backend with callback endpoint

## Installation

### Method 1: Docker Deployment (Recommended)

```bash
# Copy app to Nextcloud container
docker cp onlyoffice_callback_interceptor nextcloud-app:/var/www/html/custom_apps/

# Enter container and set permissions
docker exec -u www-data nextcloud-app php occ app:enable onlyoffice_callback_interceptor
```

### Method 2: Manual Installation

```bash
# Copy to Nextcloud apps directory
cp -r onlyoffice_callback_interceptor /path/to/nextcloud/apps/

# Set ownership
chown -R www-data:www-data /path/to/nextcloud/apps/onlyoffice_callback_interceptor

# Enable app
sudo -u www-data php /path/to/nextcloud/occ app:enable onlyoffice_callback_interceptor
```

## Configuration

1. **Access Admin Settings**
   - Go to Nextcloud admin panel
   - Navigate to **Settings** → **Additional settings**
   - Find **OnlyOffice Callback Interceptor** section

2. **Basic Settings**
   - **Django Callback URL**: `http://data.yamaguchi.lan/api/acquisition/onlyoffice/callback/`
   - **Path Filter**: `/Data/` (only intercept files in this directory)
   - **Enable Callback Interceptor**: Check to enable

3. **Security Settings**
   - **OnlyOffice Secret**: Your OnlyOffice JWT secret (e.g., `tDCVy4C0oUPWjEXCvCZ4KnFe7N7z5V`)
   - **Authentication Token**: Optional token to include in callback headers

4. **Metadata Settings**
   - **Include User Metadata**: Add user ID and display name
   - **Include Timestamp**: Add edit start timestamp

5. **Health Check Settings**
   - **Enable Health Check**: Verify Django before intercepting
   - **Health Check URL**: `http://data.yamaguchi.lan/api/acquisition/health/`
   - **Health Check Interval**: 300 seconds (default)

6. **Advanced Settings**
   - **Debug Mode**: Enable detailed logging

7. **Save Settings** and test with **Test Health Check** button

## Configuration Parameters

The app sends the following query parameters to Django callback URL:

- `nextcloud_callback`: Original Nextcloud callback URL (URL-encoded)
- `file_path`: Path of the file being edited
- `user_id`: Nextcloud user ID (if enabled)
- `user_display_name`: User's display name (if enabled)
- `edit_start_time`: ISO 8601 timestamp (if enabled)

Example callback URL:
```
http://data.yamaguchi.lan/api/acquisition/onlyoffice/callback/
  ?nextcloud_callback=http%3A%2F%2Fcloud.yamaguchi.lan%2F...
  &file_path=%2FData%2FPurchasing_abc123.xlsx
  &user_id=admin
  &user_display_name=Admin%20User
  &edit_start_time=2025-01-01T10%3A30%3A00%2B00%3A00
```

## Django Integration

Your Django backend must:

1. **Receive OnlyOffice callback** at configured endpoint
2. **Process the callback** (parse Excel, sync to database, etc.)
3. **Forward callback to Nextcloud** using the `nextcloud_callback` parameter

Example Django view:

```python
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def onlyoffice_callback(request):
    # Extract parameters
    nextcloud_callback = request.GET.get('nextcloud_callback')
    file_path = request.GET.get('file_path')

    # Process OnlyOffice callback
    callback_data = json.loads(request.body)

    # Your data processing logic here
    process_excel_data(callback_data, file_path)

    # Forward to Nextcloud
    if nextcloud_callback:
        response = requests.post(
            nextcloud_callback,
            json=callback_data,
            headers={'Content-Type': 'application/json'}
        )
        return JsonResponse(response.json(), status=response.status_code)

    return JsonResponse({'error': 0})
```

## Troubleshooting

### Callbacks not being intercepted

1. Check that app is enabled: `php occ app:list`
2. Verify settings in admin panel
3. Check path filter matches your files
4. Enable debug mode and check Nextcloud logs

### Health check failing

1. Verify Django server is running
2. Check health check URL is correct
3. Test manually: `curl http://data.yamaguchi.lan/api/acquisition/health/`
4. Check network connectivity from Nextcloud to Django

### Files not saving in Nextcloud

**Critical**: Make sure Django is forwarding callbacks to Nextcloud!

1. Check Django logs to verify forwarding
2. Verify `nextcloud_callback` parameter is being used
3. Test with debug mode enabled

### View Logs

```bash
# Nextcloud logs
tail -f /var/www/html/data/nextcloud.log

# Docker logs
docker logs -f nextcloud-app
```

## Development

### File Structure

```
onlyoffice_callback_interceptor/
├── appinfo/
│   ├── info.xml              # App metadata
│   ├── routes.php            # API routes
│   └── app.php               # (optional)
├── lib/
│   ├── AppInfo/
│   │   └── Application.php   # Main app class
│   ├── Listener/
│   │   └── OnlyOfficeConfigListener.php  # Event listener
│   ├── Service/
│   │   └── ConfigService.php # Configuration management
│   ├── Controller/
│   │   └── SettingsController.php  # Settings API
│   └── Settings/
│       └── AdminSettings.php # Admin UI
├── templates/
│   └── settings/
│       └── admin.php         # Admin settings template
├── js/
│   └── admin-settings.js     # Frontend logic
├── css/
│   └── admin-settings.css    # Styles
└── README.md
```

## Security Considerations

- ✅ Use HTTPS in production
- ✅ Set strong OnlyOffice secret
- ✅ Use authentication tokens
- ✅ Restrict path filtering to necessary directories
- ✅ Monitor logs for suspicious activity
- ✅ Keep Nextcloud and dependencies updated

## License

AGPL-3.0

## Support

For issues and questions:
- Check Nextcloud logs with debug mode enabled
- Verify Django backend is forwarding callbacks
- Test health check endpoint
- Review this README

## Version History

- **1.0.0** (2025-01-01): Initial release
  - Callback URL interception
  - JWT signing
  - Health check
  - Admin UI
