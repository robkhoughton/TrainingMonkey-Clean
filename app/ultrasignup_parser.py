"""
Ultrasignup Screenshot Parser Module
Uses Claude Vision API to extract race history from ultrasignup.com screenshots

Cost Estimate: ~$0.01-0.02 per screenshot
"""

import os
import base64
import logging
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_IMAGE_FORMATS = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp']

# Claude API configuration
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '').strip()  # Strip whitespace/newlines
ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'
CLAUDE_MODEL = 'claude-3-5-sonnet-20241022'  # Latest model with vision


def validate_image_file(file_data: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded image file
    
    Args:
        file_data: Binary file data
        filename: Original filename
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
    """
    # Check file size
    if len(file_data) > MAX_FILE_SIZE_BYTES:
        file_size_mb = len(file_data) / (1024 * 1024)
        return False, f'File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)'
    
    if len(file_data) == 0:
        return False, 'File is empty'
    
    # Check file extension
    extension = os.path.splitext(filename.lower())[1]
    if extension not in ALLOWED_EXTENSIONS:
        return False, f'Invalid file format. Allowed formats: {", ".join(ALLOWED_EXTENSIONS)}'
    
    return True, None


def encode_image_base64(file_data: bytes) -> str:
    """
    Encode image file to base64 for Claude API
    
    Args:
        file_data: Binary file data
        
    Returns:
        Base64 encoded string
    """
    return base64.standard_b64encode(file_data).decode('utf-8')


def parse_ultrasignup_screenshot(file_data: bytes, filename: str) -> Dict:
    """
    Parse ultrasignup.com screenshot using Claude Vision API
    
    Args:
        file_data: Binary image data
        filename: Original filename
        
    Returns:
        Dictionary with:
        - success: bool
        - races: List of race dicts (if success)
        - error: Error message (if not success)
        - api_cost_estimate: Estimated cost in USD
    """
    # Validate image first
    is_valid, error_message = validate_image_file(file_data, filename)
    if not is_valid:
        logger.warning(f"Image validation failed: {error_message}")
        return {
            'success': False,
            'error': error_message,
            'races': []
        }
    
    # Check API key
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not configured")
        return {
            'success': False,
            'error': 'Screenshot parsing is not configured. Please contact support.',
            'races': []
        }
    
    try:
        # Encode image
        logger.info(f"Encoding image for Claude Vision API: {filename}")
        image_base64 = encode_image_base64(file_data)
        
        # Determine media type from filename
        extension = os.path.splitext(filename.lower())[1]
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp'
        }
        media_type = media_type_map.get(extension, 'image/jpeg')
        
        # Build Claude Vision API request
        prompt = """Extract race history data from this ultrasignup.com screenshot.

For each race visible in the image, extract the following information:
- race_name: The full name of the race event (string)
- distance_miles: The race distance in miles (float, convert from km if needed)
- race_date: The race date in YYYY-MM-DD format (string)
- finish_time_minutes: The total finish time in minutes (integer)

Important guidelines:
1. Only extract races from the last 5 years
2. If distance is in kilometers, convert to miles (1 km = 0.621371 miles)
3. Convert finish times to total minutes (e.g., "5:30:45" = 330 minutes)
4. If you cannot determine a field with confidence, omit that race
5. Return ONLY valid, complete race records

Return the data as a JSON array with this exact structure:
[
  {
    "race_name": "Western States 100",
    "distance_miles": 100.0,
    "race_date": "2024-06-22",
    "finish_time_minutes": 1245
  }
]

If no valid races are found, return an empty array: []"""

        # Make API request
        logger.info("Calling Claude Vision API to parse screenshot")
        
        headers = {
            'anthropic-version': '2023-06-01',
            'x-api-key': ANTHROPIC_API_KEY,
            'content-type': 'application/json'
        }
        
        payload = {
            'model': CLAUDE_MODEL,
            'max_tokens': 4096,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'image',
                            'source': {
                                'type': 'base64',
                                'media_type': media_type,
                                'data': image_base64
                            }
                        },
                        {
                            'type': 'text',
                            'text': prompt
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(
            ANTHROPIC_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Claude API error: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f'AI parsing service error (status {response.status_code}). Please try again.',
                'races': []
            }
        
        # Parse response
        response_data = response.json()
        
        # Extract text from Claude's response
        if 'content' not in response_data or len(response_data['content']) == 0:
            logger.error("No content in Claude API response")
            return {
                'success': False,
                'error': 'No data extracted from image. Please ensure the screenshot shows race results clearly.',
                'races': []
            }
        
        # Get the text content (Claude returns array of content blocks)
        text_content = None
        for content_block in response_data['content']:
            if content_block.get('type') == 'text':
                text_content = content_block.get('text')
                break
        
        if not text_content:
            logger.error("No text content in Claude API response")
            return {
                'success': False,
                'error': 'Could not extract text from AI response',
                'races': []
            }
        
        # Parse JSON from text content
        # Claude might wrap JSON in markdown code blocks
        text_content = text_content.strip()
        if text_content.startswith('```json'):
            text_content = text_content[7:]  # Remove ```json
        if text_content.startswith('```'):
            text_content = text_content[3:]  # Remove ```
        if text_content.endswith('```'):
            text_content = text_content[:-3]  # Remove trailing ```
        text_content = text_content.strip()
        
        try:
            races = json.loads(text_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            logger.debug(f"Claude response text: {text_content}")
            return {
                'success': False,
                'error': 'Could not parse race data from image. Please ensure the screenshot is clear and shows race results.',
                'races': []
            }
        
        if not isinstance(races, list):
            logger.error(f"Expected list of races, got {type(races)}")
            return {
                'success': False,
                'error': 'Unexpected data format from image parsing',
                'races': []
            }
        
        # Validate and clean each race
        validated_races = []
        errors = []
        
        for idx, race in enumerate(races):
            is_valid, error = validate_extracted_race(race, idx + 1)
            if is_valid:
                validated_races.append(race)
            else:
                errors.append(error)
                logger.warning(f"Race {idx + 1} validation failed: {error}")
        
        # Calculate estimated cost
        # Rough estimate: ~$0.01-0.02 per image depending on size
        image_size_kb = len(file_data) / 1024
        estimated_cost = 0.01 if image_size_kb < 500 else 0.02
        
        logger.info(f"Successfully parsed {len(validated_races)} races from screenshot (cost: ${estimated_cost:.2f})")
        
        result = {
            'success': True,
            'races': validated_races,
            'api_cost_estimate': estimated_cost,
            'total_extracted': len(races),
            'total_valid': len(validated_races)
        }
        
        if errors:
            result['warnings'] = errors
        
        return result
        
    except requests.exceptions.Timeout:
        logger.error("Claude API request timed out")
        return {
            'success': False,
            'error': 'Request timed out. Please try again with a smaller image.',
            'races': []
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Claude API request failed: {str(e)}")
        return {
            'success': False,
            'error': 'Network error connecting to parsing service. Please try again.',
            'races': []
        }
    except Exception as e:
        logger.error(f"Unexpected error in parse_ultrasignup_screenshot: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f'Unexpected error during parsing: {str(e)}',
            'races': []
        }


def validate_extracted_race(race: Dict, race_number: int = 0) -> Tuple[bool, Optional[str]]:
    """
    Validate a single extracted race record
    
    Args:
        race: Dictionary with race data
        race_number: Race index for error messages
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
    """
    race_label = f"Race {race_number}" if race_number > 0 else "Race"
    
    # Check required fields
    required_fields = ['race_name', 'distance_miles', 'race_date', 'finish_time_minutes']
    for field in required_fields:
        if field not in race:
            return False, f"{race_label}: Missing required field '{field}'"
    
    # Validate race_name
    if not isinstance(race['race_name'], str) or not race['race_name'].strip():
        return False, f"{race_label}: race_name must be a non-empty string"
    
    # Validate distance_miles
    try:
        distance = float(race['distance_miles'])
        if distance <= 0:
            return False, f"{race_label}: distance_miles must be greater than 0"
        if distance > 200:
            return False, f"{race_label}: distance_miles seems unrealistic ({distance} miles)"
        # Update the race dict with validated float
        race['distance_miles'] = distance
    except (ValueError, TypeError):
        return False, f"{race_label}: distance_miles must be a valid number"
    
    # Validate finish_time_minutes
    try:
        finish_time = int(race['finish_time_minutes'])
        if finish_time <= 0:
            return False, f"{race_label}: finish_time_minutes must be greater than 0"
        if finish_time > 10080:  # 7 days in minutes
            return False, f"{race_label}: finish_time_minutes seems unrealistic ({finish_time} minutes)"
        # Update the race dict with validated int
        race['finish_time_minutes'] = finish_time
    except (ValueError, TypeError):
        return False, f"{race_label}: finish_time_minutes must be a valid integer"
    
    # Validate race_date
    try:
        race_date = datetime.strptime(race['race_date'], '%Y-%m-%d').date()
        
        # Check if within last 5 years
        today = datetime.now().date()
        five_years_ago = today - timedelta(days=5*365)
        
        if race_date < five_years_ago:
            return False, f"{race_label}: race_date is older than 5 years"
        
        if race_date > today:
            return False, f"{race_label}: race_date is in the future"
        
    except (ValueError, TypeError):
        return False, f"{race_label}: race_date must be in format YYYY-MM-DD"
    
    return True, None

