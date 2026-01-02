# Salamoonder API Python Wrapper

This is a Python wrapper for interacting with the Salamoonder API. It simplifies the process of creating tasks and retrieving task results using Salamoonder's services.

## Installation

To use this wrapper in your project, simply copy the `salamoonder` folder into your project directory.

## Usage

### Initialization

To use the Salamoonder API wrapper, first initialize an instance of the `salamoonder` class with your API key:

```python
client = Salamoonder("YOUR_KEY_HERE")
```
# Example: Creating a KasadaCaptchaSolver task
```python
task_id = client.task.createTask(
    task_type="KasadaCaptchaSolver", 
    pjs_url="https://k.twitchcdn.net/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/p.js",
    cd_only="false"
)
```

# Example: Creating a Twitch_PublicIntegrity task
```python
task_id = client.task.createTask(
    task_type="Twitch_PublicIntegrity", 
    access_token="YOUR_ACCESS_TOKEN", 
    device_id="Optional", 
    client_id="Optional"
)
```

# Example: Creating a IncapsulaReese84Solver task
```python
task_id = client.task.createTask(
    task_type="IncapsulaReese84Solver", 
    website="https://www.pokemoncenter.com/", 
    submit_payload=True
)
```

# Example: Creating a IncapsulaUTMVCSolver task
```python
task_id = client.task.createTask(
    task_type="IncapsulaUTMVCSolver", 
    website="https://group.accor.com/"
)
```

# Example: Creating a AkamaiWebSensorSolver task
```python
task_id = client.task.createTask(
    task_type="AkamaiWebSensorSolver",
    url="",
    abck="",
    bmsz="",
    script="",
    sensor_url="",
    user_agent="",
    count=0,
    data=""
)
```

# Example: Creating a AkamaiSBSDSolver task
```python
task_id = client.task.createTask(
    task_type="AkamaiSBSDSolver",
    url="",
    cookie="",
    sbsd_url="",
    script=""
)
```

# Example: Creating a DataDomeInterstitialSolver task
```python
task_id = client.task.createTask(
    task_type="DataDomeInterstitialSolver",
    captcha_url="https://geo.captcha-delivery.com/interstitial/...",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebK...",
    country_code="us"
)
```

# Example: Creating a DataDomeSliderSolver task
```python
task_id = client.task.createTask(
    task_type="DataDomeSliderSolver",
    captcha_url="https://geo.captcha-delivery.com/captcha/...",
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64  ...",
    country_code="us"
)
```

# Example: Retrieving task result
```python
result = client.task.getTaskResult(task_id)
print("Solution:", result)
```
## Support

If you need any help, please reach out to our support members on Telegram [here](https://t.me/salamoonder_bot).
