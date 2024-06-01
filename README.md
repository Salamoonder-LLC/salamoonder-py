# Salamoonder API Python Wrapper

This is a Python wrapper for interacting with the Salamoonder API. It simplifies the process of creating tasks and retrieving task results using Salamoonder's services.

## Installation

To use this wrapper in your project, simply copy the `salamoonder.py` file into your project directory.

## Usage

### Initialization

To use the Salamoonder API wrapper, first initialize an instance of the `salamoonder` class with your API key:

```python
salamoonder_api = salamoonder(api_key="YOUR_API_KEY_HERE")
```
# Example: Creating a KasadaCaptchaSolver task
```python
task_id = salamoonder_api.createTask(
    task_type="KasadaCaptchaSolver", 
    pjs_url="https://k.twitchcdn.net/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/p.js",
    cd_only="false"
)
```

# Example: Creating a Twitch_CheckIntegrity task
```python
task_id = salamoonder_api.createTask(
    task_type="Twitch_CheckIntegrity", 
    token="v4.public_token"
)
```

# Example: Creating a Twitch_PublicIntegrity task
```python
task_id = salamoonder_api.createTask(
    task_type="Twitch_PublicIntegrity", 
    access_token="YOUR_ACCESS_TOKEN", 
    proxy="ip:port", 
    device_id="Optional", 
    client_id="Optional"
)
```

# Example: Creating a Twitch_RegisterAccount task
```python
task_id = salamoonder_api.createTask(
    task_type="Twitch_RegisterAccount", 
    email="example@gmail.com"
)
```

# Example: Retrieving task result
```python
solution = salamoonder_api.getTaskResult("YOUR_API_KEY_HERE", task_id)
print("Solution:", solution)
```
## Support

If you need any help, please reach out to our support members on Telegram [here](https://t.me/salamoonder).
