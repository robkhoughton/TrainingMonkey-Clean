#!/usr/bin/env python3
"""
Secrets management utility for Training Monkey™
Handles Google Secret Manager integration
"""

import os
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


def get_secret(secret_name, project_id=None):
    """Get secret from Google Secret Manager"""
    try:
        if not project_id:
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'dev-ruler-460822-e8')

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error getting secret {secret_name}: {str(e)}")
        return None
