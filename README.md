# Salamoonder SDK

A straightforward Python wrapper for Salamoonder's API, designed for easy integration and async usage. Perfect for solving captchas and bypassing bot detection on various platforms.

[![PyPI version](https://badge.fury.io/py/salamoonder-sdk.svg)](https://badge.fury.io/py/salamoonder)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Simple and intuitive async API
- Support for multiple captcha types:
  - Akamai Web Sensor
  - Akamai SBSD (Sensor Based Script Detection)
  - Kasada protection bypass
  - DataDome (Slider & Interstitial)
  - Incapsula/Imperva
  - Twitch Public Integrity
- Fully async with `async`/`await` patterns
- Comprehensive error handling and logging
- Modern Python with full type hints
- Production-ready with proper resource management

## Installation

```bash
pip install salamoonder
```

## Requirements

- Python >= 3.8

## Quick Start

```python
import asyncio
from salamoonder import Salamoonder

async def main():
    async with Salamoonder('YOUR_API_KEY') as client:
        # Create and solve a Kasada captcha task
        task_id = await client.task.createTask('KasadaCaptchaSolver', 
            pjs_url='https://example.com/script.js',
            cd_only="false"
        )
        
        # Poll for the result
        solution = await client.task.getTaskResult(task_id)
        print('Solution:', solution)

asyncio.run(main())
```

## Usage Examples

### Akamai Web Sensor

```python
async with Salamoonder('YOUR_API_KEY') as client:
    task_id = await client.task.createTask('AkamaiWebSensorSolver',
        url='https://example.com',
        abck='abck_cookie_value',
        bmsz='bmsz_cookie_value', 
        script='sensor_script_content',
        sensor_url='https://sensor.example.com/sensor.js',
        count=0,
        data='sensor_data',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)...'
    )
    
    result = await client.task.getTaskResult(task_id, interval=2)  # Poll every 2 seconds
    print('Result:', result)
```

### Kasada

```python
async with Salamoonder('YOUR_API_KEY') as client:
    # Kasada Captcha  
    captcha_task_id = await client.task.createTask('KasadaCaptchaSolver',
        pjs_url='https://example.com/script.js',
        cd_only="false"
    )
    captcha_result = await client.task.getTaskResult(captcha_task_id)
    
    # Kasada Payload
    payload_task_id = await client.task.createTask('KasadaPayloadSolver',
        url='https://example.com',
        script_content='script_content_here',
        script_url='https://example.com/script.js'
    )
    payload_result = await client.task.getTaskResult(payload_task_id)
```

### DataDome

```python
async with Salamoonder('YOUR_API_KEY') as client:
    # Slider captcha
    slider_task_id = await client.task.createTask('DataDomeSliderSolver',
        captcha_url='https://captcha.example.com/slider',
        country_code='US',
        user_agent='Mozilla/5.0...'
    )
    slider_result = await client.task.getTaskResult(slider_task_id)
    
    # Interstitial captcha  
    interstitial_task_id = await client.task.createTask('DataDomeInterstitialSolver',
        captcha_url='https://captcha.example.com/interstitial',
        country_code='US'
    )
    interstitial_result = await client.task.getTaskResult(interstitial_task_id)
```

### Direct Client Methods

For custom HTTP requests with TLS client impersonation:

```python
async with Salamoonder('YOUR_API_KEY') as client:
    # GET request
    response = await client.get('https://example.com', 
        headers={'User-Agent': 'Custom UA'},
        proxy='http://proxy:port'
    )
    
    # POST request
    post_response = await client.post('https://example.com/api',
        json={'key': 'value'},
        headers={'Content-Type': 'application/json'}
    )
```

## API Reference

### Salamoonder Class

Main entry point for the library.

```python
async with Salamoonder(api_key, base_url=None, impersonate=None) as client:
    # Your code here
    pass
```

**Parameters:**
- `api_key` (str) - Your Salamoonder API key (required)
- `base_url` (str) - API base URL (default: `https://salamoonder.com/api`)
- `impersonate` (str) - Browser to impersonate (default: `chrome133a`)

**Properties:**
- `task` - Tasks API instance (recommended for solving captchas)
- `akamai`, `akamai_sbsd`, `datadome`, `kasada` - Low-level solver instances (advanced use only)
- `session` - Session information and cookies

**Methods:**
- `get(url, **kwargs)` - Make a GET request
- `post(url, **kwargs)` - Make a POST request

## Supported Anti-Bot Solutions

### 🔒 Kasada
- Script extraction and parsing
- Payload solving  
- Challenge submission

### 🛡️ Akamai Bot Manager
- Web sensor data extraction
- SBSD (Sensor Based Script Detection) support
- Cookie management

### 🔐 DataDome
- Slider captcha URL parsing
- Interstitial challenge support

## Supported Captcha Types

- `KasadaCaptchaSolver`
- `KasadaPayloadSolver`
- `AkamaiWebSensorSolver`
- `AkamaiSBSDSolver`
- `DataDomeSliderSolver`
- `DataDomeInterstitialSolver`
- `IncapsulaReese84Solver`
- `IncapsulaUTMVCSolver` 
- `Twitch_PublicIntegrity`

## Module Exports

You can import individual modules if needed:

```python
# Main class and main exports
from salamoonder import Salamoonder
from salamoonder.tasks import Tasks
from salamoonder.client import Client

# Error classes
from salamoonder.client import APIError, MissingAPIKeyError

# For advanced/low-level operations only
from salamoonder.utils.akamai import AkamaiWeb, AkamaiSBSD
from salamoonder.utils.datadome import Datadome
from salamoonder.utils.kasada import Kasada
```

**Note:** The utility classes (`AkamaiWeb`, `AkamaiSBSD`, `Datadome`, `Kasada`) are for low-level operations. For most use cases, use the Tasks API through the main client.

## Error Handling

```python
import asyncio
from salamoonder import Salamoonder
from salamoonder.client import APIError, MissingAPIKeyError

async def main():
    try:
        async with Salamoonder('YOUR_API_KEY') as client:
            task_id = await client.task.createTask('KasadaCaptchaSolver',
                pjs_url='https://example.com/script.js',
                cd_only="false"
            )
            result = await client.task.getTaskResult(task_id)
    except MissingAPIKeyError:
        print('API key is required')
    except APIError as error:
        print('API error:', error)
    except Exception as error:
        print('Unexpected error:', error)

asyncio.run(main())
```

## Configuration

### Custom Base URL
```python
async with Salamoonder(
    api_key='your_key',
    base_url='https://custom-api.salamoonder.com/api'
) as client:
    pass
```

### Browser Impersonation  
```python
async with Salamoonder(
    api_key='your_key', 
    impersonate='chrome133a'  # or firefox, safari
) as client:
    # Requests will impersonate the specified browser
    pass
```

### Proxy Support
```python
# All methods support proxy parameter
result = await client.akamai.fetch_and_extract(
    website_url='https://example.com',
    user_agent='Mozilla/5.0...',
    proxy='http://username:password@proxy.example.com:8080'
)
```

## Logging

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all salamoonder operations will show debug info
async with Salamoonder(api_key='key') as client:
    # Debug logs will show HTTP requests, responses, etc.
    await client.task.createTask(...)
```

## Performance Tips

- Use async context managers (`async with`) for automatic resource cleanup
- Reuse the same client instance for multiple operations
- Process multiple tasks concurrently with `asyncio.gather()`

```python
# Good: Reuse client for multiple operations
async with Salamoonder(api_key='key') as client:
    task1 = await client.task.createTask(...)
    task2 = await client.task.createTask(...)
    
    # Wait for both results concurrently
    results = await asyncio.gather(
        client.task.getTaskResult(task1),
        client.task.getTaskResult(task2)
    )
```

## License

MIT - See [LICENSE](LICENSE) file for details

## Support

For issues, feature requests, or questions, please visit:
- **Website**: [salamoonder.com](https://salamoonder.com)
- **Documentation**: [salamoonder.com/docs](https://apidocs.salamoonder.com)
- **Support**: [support@salamoonder.com](mailto:support@salamoonder.com)
- **Telegram**: [Text us!](https://t.me/salamoonder_bot)
