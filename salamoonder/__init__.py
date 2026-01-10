import logging
from .client import Client
from .tasks import Tasks
from .utils import AkamaiWeb, Datadome, AkamaiSBSD

# Configure package logger with console output
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class Salamoonder:
    """Main Salamoonder SDK client.
    
    Args:
        api_key: Your Salamoonder API key
        
    Example:
        >>> client = Salamoonder(api_key="your_api_key")
        >>> 
        >>> # Use tasks
        >>> task_id = client.task.createTask("KasadaCaptchaSolver", pjs_url="...")
        >>> result = client.task.getTaskResult(task_id)
        >>> 
        >>> # Use utils
        >>> sensor_data = client.akamai.fetch_and_extract(
        ...     url="https://example.com",
        ...     proxy="http://proxy:8080"
        ... )
    """
    
    def __init__(self, api_key):
        self._client = Client(api_key)

        self.task = Tasks(self._client)

        self.akamai = AkamaiWeb(self._client)
        self.akamai_sbsd = AkamaiSBSD(self._client)
        self.datadome = Datadome(self._client)

    def get(self, *args, **kwargs):
        return self._client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self._client.post(*args, **kwargs)

    @property
    def session(self):
        return self._client.session