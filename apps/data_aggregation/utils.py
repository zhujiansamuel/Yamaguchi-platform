"""
Utility functions for data_aggregation app.
"""
import requests
from django.conf import settings
from django.apps import apps
from .excel_exporters import get_exporter, get_dashboard_exporter
import httpx



def get_all_model_names():
    """
    Get all model names from data_aggregation app.
    返回data_aggregation app的所有模型名称。
    """
    app_config = apps.get_app_config('data_aggregation')
    models = app_config.get_models()
    return [model.__name__ for model in models]


def export_model_to_excel(model_name):
    """
    Export a specific model's data to Excel format.
    将指定模型的数据导出为Excel格式。

    This function now uses the new excel_exporters architecture,
    which provides fine-grained control over Excel export for each model.

    Args:
        model_name (str): Name of the model to export

    Returns:
        io.BytesIO: Excel file as bytes stream

    Raises:
        ValueError: If no exporter is found for the model
    """
    # Get the appropriate exporter for the model
    exporter = get_exporter(model_name)

    # Use the exporter to generate the Excel file
    return exporter.export()


def ensure_nextcloud_directory(directory_path, auth):
    """
    Ensure a directory exists in Nextcloud, create if it doesn't.
    确保Nextcloud中存在目录，如果不存在则创建。

    Args:
        directory_path (str): Full WebDAV URL to the directory
        auth (tuple): Authentication tuple (username, password)

    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        # Check if directory exists using PROPFIND
        response = requests.request(
            'PROPFIND',
            directory_path,
            auth=auth,
            timeout=10
        )

        # If directory exists, return True
        if response.status_code in [200, 207]:
            return True

        # If directory doesn't exist (404), try to create it
        if response.status_code == 404:
            response = requests.request(
                'MKCOL',
                directory_path,
                auth=auth,
                timeout=10
            )

            # 201 means created successfully, 405 means already exists
            if response.status_code in [201, 405]:
                return True

        return False
    except Exception:
        # If there's an error, try to create anyway
        try:
            response = requests.request(
                'MKCOL',
                directory_path,
                auth=auth,
                timeout=10
            )
            return response.status_code in [201, 405]
        except Exception:
            return False


def upload_to_nextcloud(file_content, filename, directory_path=None):
    """
    Upload file to Nextcloud using WebDAV.
    使用WebDAV将文件上传到Nextcloud。

    Args:
        file_content (bytes): File content as bytes
        filename (str): Name of the file to upload
        directory_path (str, optional): Directory path to upload to.
                                       If not provided, uses EXCEL_OUTPUT_PATH from settings.

    Returns:
        dict: Upload result with status and message
    """
    config = settings.NEXTCLOUD_CONFIG
    auth = (config['webdav_login'], config['webdav_password'])

    # Use provided directory path or default to EXCEL_OUTPUT_PATH
    target_path = directory_path if directory_path is not None else settings.EXCEL_OUTPUT_PATH

    # Ensure the directory exists
    directory_url = config['webdav_hostname'] + target_path.rstrip('/')
    if not ensure_nextcloud_directory(directory_url, auth):
        return {
            'status': 'error',
            'message': f'Failed to create or access directory: {directory_url}'
        }

    # Construct file URL
    webdav_url = config['webdav_hostname'] + target_path + filename

    try:
        response = requests.put(
            webdav_url,
            data=file_content,
            auth=auth,
            headers={'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
            timeout=30
        )

        if response.status_code in [200, 201, 204]:
            return {
                'status': 'success',
                'message': f'File uploaded successfully to {webdav_url}',
                'url': webdav_url
            }
        else:
            return {
                'status': 'error',
                'message': f'Upload failed with status code {response.status_code}',
                'details': response.text
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Upload failed: {str(e)}'
        }


def download_from_nextcloud(filename, directory_path=None):
    """
    Download file from Nextcloud using WebDAV.
    使用WebDAV从Nextcloud下载文件。

    Args:
        filename (str): Name of the file to download
        directory_path (str, optional): Directory path to download from.
                                       If not provided, uses EXCEL_OUTPUT_PATH from settings.

    Returns:
        dict: Download result with status, message, and content (bytes) if successful
    """
    config = settings.NEXTCLOUD_CONFIG
    auth = (config['webdav_login'], config['webdav_password'])

    # Use provided directory path or default to EXCEL_OUTPUT_PATH
    target_path = directory_path if directory_path is not None else settings.EXCEL_OUTPUT_PATH

    # Construct file URL
    webdav_url = config['webdav_hostname'] + target_path + filename

    try:
        response = requests.get(
            webdav_url,
            auth=auth,
            timeout=30
        )

        if response.status_code == 200:
            return {
                'status': 'success',
                'message': f'File downloaded successfully from {webdav_url}',
                'content': response.content,
                'url': webdav_url
            }
        elif response.status_code == 404:
            return {
                'status': 'not_found',
                'message': f'File not found: {webdav_url}'
            }
        else:
            return {
                'status': 'error',
                'message': f'Download failed with status code {response.status_code}',
                'details': response.text
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Download failed: {str(e)}'
        }


def find_file_in_nextcloud(filename_pattern, directory_path=None):
    """
    Find a file in Nextcloud directory that matches the pattern.
    在Nextcloud目录中查找匹配模式的文件。

    Args:
        filename_pattern (str): Filename pattern to search for (e.g., "iPhone inventory")
                               Will match files starting with this pattern, regardless of extension.
        directory_path (str, optional): Directory path to search in.
                                       If not provided, uses EXCEL_OUTPUT_PATH_DASHBOARD from settings.

    Returns:
        dict: Result with status and matched filename if found
    """
    import xml.etree.ElementTree as ET
    
    config = settings.NEXTCLOUD_CONFIG
    auth = (config['webdav_login'], config['webdav_password'])

    # Use provided directory path or default to EXCEL_OUTPUT_PATH_DASHBOARD
    target_path = directory_path if directory_path is not None else settings.EXCEL_OUTPUT_PATH_DASHBOARD

    # Construct directory URL
    directory_url = config['webdav_hostname'] + target_path.rstrip('/')

    try:
        # Use PROPFIND to list directory contents
        response = requests.request(
            'PROPFIND',
            directory_url,
            auth=auth,
            headers={'Depth': '1'},
            timeout=10
        )

        if response.status_code not in [200, 207]:
            return {
                'status': 'error',
                'message': f'Failed to list directory: {directory_url}'
            }

        # Parse XML response
        root = ET.fromstring(response.content)
        ns = {'d': 'DAV:'}
        
        # Find all href elements
        for response_elem in root.findall('.//d:response', ns):
            href = response_elem.find('d:href', ns)
            if href is not None:
                # Extract filename from href
                href_text = href.text
                if href_text:
                    # Get the last part of the path
                    parts = href_text.rstrip('/').split('/')
                    if parts:
                        file_name = parts[-1]
                        # URL decode the filename
                        from urllib.parse import unquote
                        file_name = unquote(file_name)
                        
                        # Check if filename matches pattern (case-insensitive, any extension)
                        if file_name.lower().startswith(filename_pattern.lower()):
                            return {
                                'status': 'found',
                                'filename': file_name,
                                'message': f'Found file: {file_name}'
                            }

        return {
            'status': 'not_found',
            'message': f'No file matching pattern "{filename_pattern}" found in {directory_url}'
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Search failed: {str(e)}'
        }


def upload_excel_files(file_content, model_name, timestamp=None):
    """
    Upload Excel file to both historical and non-historical directories.
    上传Excel文件到历史追溯和非历史追溯目录。

    This function uploads the Excel file to two locations:
    1. No_aggregated_raw_data/ - Latest version without timestamp (always)
    2. data_platform/ - Historical version with timestamp (if enabled)

    Args:
        file_content (bytes): Excel file content as bytes
        model_name (str): Name of the model being exported
        timestamp (str, optional): Timestamp string for historical filename.
                                  If not provided and historical tracking is enabled,
                                  current timestamp will be generated.

    Returns:
        dict: Upload results with status and details for both uploads
    """
    from datetime import datetime

    results = {
        'non_historical': None,
        'historical': None,
        'overall_status': 'success'
    }

    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. Always upload to No_aggregated_raw_data directory (WITH timestamp)
    # Note: User requested No_aggregated_raw_data to have timestamped files
    non_historical_filename = f"{model_name}_test_{timestamp}.xlsx"
    results['non_historical'] = upload_to_nextcloud(
        file_content,
        non_historical_filename,
        directory_path=settings.EXCEL_OUTPUT_PATH_NO_HISTORY
    )

    if results['non_historical']['status'] != 'success':
        results['overall_status'] = 'partial_success'

    # 2. Optionally upload to data_platform directory (WITHOUT timestamp, overwrites existing)
    # Note: User requested data_platform to have files WITHOUT timestamp
    if settings.ENABLE_EXCEL_HISTORICAL_TRACKING:
        historical_filename = f"{model_name}_test.xlsx"
        results['historical'] = upload_to_nextcloud(
            file_content,
            historical_filename,
            directory_path=settings.EXCEL_OUTPUT_PATH
        )

        if results['historical']['status'] != 'success':
            results['overall_status'] = 'partial_success'
    else:
        results['historical'] = {
            'status': 'skipped',
            'message': 'Historical tracking is disabled'
        }

    # Determine overall status
    if (results['non_historical']['status'] == 'error' and
        (results['historical']['status'] == 'error' or results['historical']['status'] == 'skipped')):
        results['overall_status'] = 'error'

    return results


def export_iphone_inventory_dashboard():
    """
    Export iPhone inventory data to Dashboard Excel file in Nextcloud.
    导出iPhone库存数据到Nextcloud的Dashboard Excel文件。

    This function:
    1. Checks if "iPhone inventory" file exists in Data_Dashboard folder (any extension)
    2. If exists, downloads it and writes data to existing file
    3. If not exists, creates a new file
    4. Uploads the file back to Nextcloud

    Returns:
        dict: Export result with status and details
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Get the dashboard exporter
    exporter = get_dashboard_exporter('iPhoneInventoryDashboard')
    
    # Define the filename pattern and default filename
    filename_pattern = 'iPhone inventory'
    default_filename = 'iPhone inventory.xlsx'
    
    # Check if file exists in Data_Dashboard folder
    find_result = find_file_in_nextcloud(
        filename_pattern,
        directory_path=settings.EXCEL_OUTPUT_PATH_DASHBOARD
    )
    
    existing_file_bytes = None
    target_filename = default_filename
    
    if find_result['status'] == 'found':
        # File exists, download it
        target_filename = find_result['filename']
        logger.info(f"Found existing file: {target_filename}")
        
        download_result = download_from_nextcloud(
            target_filename,
            directory_path=settings.EXCEL_OUTPUT_PATH_DASHBOARD
        )
        
        if download_result['status'] == 'success':
            existing_file_bytes = download_result['content']
            logger.info(f"Downloaded existing file: {target_filename}")
        else:
            logger.warning(f"Failed to download existing file, creating new: {download_result['message']}")
    elif find_result['status'] == 'not_found':
        logger.info(f"File not found, will create new file: {default_filename}")
    else:
        logger.warning(f"Error searching for file: {find_result['message']}")
    
    # Export data
    try:
        excel_output = exporter.export(existing_file_bytes=existing_file_bytes)
        excel_bytes = excel_output.getvalue()
    except Exception as e:
        logger.error(f"Failed to export data: {str(e)}")
        return {
            'status': 'error',
            'message': f'Failed to export data: {str(e)}'
        }
    
    # Upload to Nextcloud
    upload_result = upload_to_nextcloud(
        excel_bytes,
        target_filename,
        directory_path=settings.EXCEL_OUTPUT_PATH_DASHBOARD
    )
    
    if upload_result['status'] == 'success':
        return {
            'status': 'success',
            'message': f'Successfully exported iPhone inventory to {target_filename}',
            'filename': target_filename,
            'url': upload_result.get('url'),
            'file_existed': existing_file_bytes is not None
        }
    else:
        return {
            'status': 'error',
            'message': f'Failed to upload file: {upload_result["message"]}',
            'details': upload_result.get('details')
        }


def _check_token(request, path_token=None):
    """
    检查 webhook token 是否有效。
    
    Args:
        request: DRF request 对象
        path_token: 路径中的 token（可选）
    
    Returns:
        bool: Token 是否有效
    """
    from django.conf import settings
    
    # 从多个位置获取 token
    token = (
        request.headers.get('X-Webhook-Token') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        request.query_params.get('token') or
        request.query_params.get('t') or
        (request.data.get('token') if hasattr(request, 'data') else None) or
        path_token
    )
    
    # 获取配置的 token（可以使用 WEBSCRAPER_WEBHOOK_TOKEN 或 BATCH_STATS_API_TOKEN）
    expected_token = getattr(settings, 'WEBSCRAPER_WEBHOOK_TOKEN', None) or \
                     getattr(settings, 'BATCH_STATS_API_TOKEN', None)
    
    if not expected_token:
        return False
    
    return token == expected_token


def _resolve_source(request) -> str | None:
    """优先 body/query 的 source；否则用 sitemap_name/custom_id → WEB_SCRAPER_SOURCE_MAP"""
    source_name = request.query_params.get("source")
    if not source_name and isinstance(request.data, dict):
        source_name = request.data.get("source")
    if source_name:
        return source_name
    # 映射
    sitemap_name = (request.data.get("sitemap_name") or request.data.get("sitemap") or "") if isinstance(
        request.data, dict) else ""
    custom_id = (request.data.get("custom_id") or "") if isinstance(request.data, dict) else ""
    mp = getattr(settings, "WEB_SCRAPER_SOURCE_MAP", {})

    # Try exact match first
    source = mp.get(sitemap_name) or mp.get(custom_id)
    if source:
        return source

    # Try custom_id prefix matching with TRACKING_TASK_CONFIGS
    if custom_id:
        from apps.data_acquisition.tasks import TRACKING_TASK_CONFIGS
        for task_name, config in TRACKING_TASK_CONFIGS.items():
            prefix = config.get('custom_id_prefix', '')
            if prefix and custom_id.startswith(f"{prefix}-"):
                return task_name

    return None


TIMEOUT = 60
def fetch_webscraper_export_sync(job_id: str, *, format: str = "csv") -> bytes:
    """
    Fetch export data from WebScraper.io API.

    Args:
        job_id: The WebScraper job ID
        format: Export format (default: "csv")

    Returns:
        bytes: The exported data content

    Raises:
        RuntimeError: If API token or URL template is not configured
        httpx.HTTPStatusError: If the API request fails
    """
    token = getattr(settings, "WEB_SCRAPER_API_TOKEN", "")
    tpl   = getattr(settings, "WEB_SCRAPER_EXPORT_URL_TEMPLATE", "")
    if not token or not tpl:
        raise RuntimeError("WEB_SCRAPER_API_TOKEN / WEB_SCRAPER_EXPORT_URL_TEMPLATE 未配置")

    # Build URL with job_id
    url = tpl.format(job_id=job_id)

    # WebScraper.io API uses api_token as query parameter, not Bearer header
    separator = "&" if "?" in url else "?"
    url = f"{url}{separator}api_token={token}"

    with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content
