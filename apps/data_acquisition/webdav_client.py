"""
WebDAV client for Nextcloud integration.
Handles file operations via WebDAV protocol using requests library.
"""
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple
from datetime import datetime
from io import BytesIO

import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

logger = logging.getLogger(__name__)


class NextcloudWebDAVClient:
    """
    WebDAV client for Nextcloud file operations using requests library.
    """

    def __init__(self):
        """Initialize WebDAV client with settings from Django config."""
        self.webdav_url = settings.NEXTCLOUD_WEBDAV_URL.rstrip('/')
        self.username = settings.NEXTCLOUD_USERNAME
        self.password = settings.NEXTCLOUD_PASSWORD
        self.timeout = settings.NEXTCLOUD_TIMEOUT
        self.auth = HTTPBasicAuth(self.username, self.password)

        # WebDAV namespaces
        self.ns = {
            'd': 'DAV:',
            'oc': 'http://owncloud.org/ns',
            'nc': 'http://nextcloud.org/ns'
        }

    def get_file_info(self, file_path: str) -> Optional[Dict[str, str]]:
        """
        Get file metadata using PROPFIND.

        Args:
            file_path: Nextcloud file path (e.g., /Data/Purchasing_abc123.xlsx)

        Returns:
            Dictionary with 'etag' and 'modified' keys, or None if file not found

        Example:
            {'etag': '"5f9c8b2a1d3e4"', 'modified': '2025-01-15T10:30:00Z'}
        """
        try:
            url = f"{self.webdav_url}{file_path}"

            # PROPFIND request body
            propfind_body = '''<?xml version="1.0" encoding="utf-8" ?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:getetag/>
    <d:getlastmodified/>
    <d:getcontentlength/>
  </d:prop>
</d:propfind>'''

            response = requests.request(
                'PROPFIND',
                url,
                auth=self.auth,
                data=propfind_body,
                headers={'Content-Type': 'application/xml', 'Depth': '0'},
                timeout=self.timeout
            )

            if response.status_code not in [207, 200]:
                logger.error(f"PROPFIND failed for {file_path}: {response.status_code}")
                return None

            # Parse XML response
            root = ET.fromstring(response.content)

            # Extract etag
            etag_elem = root.find('.//d:getetag', self.ns)
            etag = etag_elem.text.strip('"') if etag_elem is not None and etag_elem.text else ''

            # Extract last modified
            modified_elem = root.find('.//d:getlastmodified', self.ns)
            modified = None
            if modified_elem is not None and modified_elem.text:
                try:
                    from email.utils import parsedate_to_datetime
                    modified = parsedate_to_datetime(modified_elem.text)
                except Exception as e:
                    logger.warning(f"Could not parse modified date: {modified_elem.text}, {e}")

            # Extract size
            size_elem = root.find('.//d:getcontentlength', self.ns)
            size = int(size_elem.text) if size_elem is not None and size_elem.text else 0

            return {
                'etag': etag,
                'modified': modified,
                'size': size,
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error getting file info for {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file info for {file_path}: {e}")
            return None

    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download file content using WebDAV GET.

        Args:
            file_path: Nextcloud file path

        Returns:
            File content as bytes, or None if download failed
        """
        try:
            url = f"{self.webdav_url}{file_path}"

            response = requests.get(
                url,
                auth=self.auth,
                timeout=self.timeout,
                stream=True
            )

            if response.status_code != 200:
                logger.error(f"GET failed for {file_path}: {response.status_code}")
                return None

            return response.content

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error downloading file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading file {file_path}: {e}")
            return None

    def upload_file(self, file_path: str, content: bytes, check_etag: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Upload file content using WebDAV PUT.

        Args:
            file_path: Nextcloud file path
            content: File content as bytes
            check_etag: If provided, only upload if current etag matches (prevents overwriting concurrent edits)

        Returns:
            Tuple of (success: bool, new_etag: Optional[str])
            - If check_etag provided and doesn't match, returns (False, current_etag)
            - If upload successful, returns (True, new_etag)
            - If error, returns (False, None)
        """
        try:
            # If etag check requested, verify current etag
            if check_etag:
                current_info = self.get_file_info(file_path)
                if current_info and current_info['etag'] != check_etag:
                    logger.warning(
                        f"ETag mismatch for {file_path}: "
                        f"expected {check_etag}, found {current_info['etag']}"
                    )
                    return (False, current_info['etag'])

            # Upload file
            url = f"{self.webdav_url}{file_path}"

            headers = {}
            if check_etag:
                headers['If-Match'] = f'"{check_etag}"'

            response = requests.put(
                url,
                auth=self.auth,
                data=content,
                headers=headers,
                timeout=self.timeout
            )

            if response.status_code not in [200, 201, 204]:
                logger.error(f"PUT failed for {file_path}: {response.status_code}")
                return (False, None)

            # Get new etag from response header or re-fetch
            new_etag = response.headers.get('ETag', '').strip('"')
            if not new_etag:
                new_info = self.get_file_info(file_path)
                new_etag = new_info['etag'] if new_info else None

            logger.info(f"Successfully uploaded file {file_path}, new etag: {new_etag}")
            return (True, new_etag)

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error uploading file {file_path}: {e}")
            return (False, None)
        except Exception as e:
            logger.error(f"Unexpected error uploading file {file_path}: {e}")
            return (False, None)

    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in Nextcloud.

        Args:
            file_path: Nextcloud file path

        Returns:
            True if file exists, False otherwise
        """
        try:
            info = self.get_file_info(file_path)
            return info is not None
        except Exception as e:
            logger.error(f"Error checking file existence for {file_path}: {e}")
            return False

    def create_directory(self, dir_path: str) -> bool:
        """
        Create directory if it doesn't exist.

        Args:
            dir_path: Directory path

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.webdav_url}{dir_path}"

            response = requests.request(
                'MKCOL',
                url,
                auth=self.auth,
                timeout=self.timeout
            )

            if response.status_code in [201, 405]:  # 405 = already exists
                logger.info(f"Directory ready: {dir_path}")
                return True
            else:
                logger.error(f"MKCOL failed for {dir_path}: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error creating directory {dir_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating directory {dir_path}: {e}")
            return False
