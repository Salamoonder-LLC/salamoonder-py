import logging
from .client import Client
from .tasks import Tasks
from .utils import AkamaiWeb, Datadome, AkamaiSBSD, Kasada

# Package metadata
__version__ = "1.0.0"
__author__ = "Salamoonder"
__email__ = "support@salamoonder.com"
__license__ = "MIT"
__url__ = "https://github.com/Salamoonder-LLC/salamoonder-py"

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
        >>> async with Salamoonder(api_key="your_api_key") as client:
        ...     # Use tasks
        ...     task_id = await client.task.createTask("KasadaCaptchaSolver", pjs_url="...")
        ...     result = await client.task.getTaskResult(task_id)
        ...     
        ...     # Use utils
        ...     sensor_data = await client.akamai.fetch_and_extract(
        ...         url="https://example.com",
        ...         proxy="http://proxy:8080"
        ...     )
    """
    
    def __init__(self, api_key):
        self._client = Client(api_key)

        self.task = Tasks(self._client)

        self.akamai = AkamaiWeb(self._client)
        self.akamai_sbsd = AkamaiSBSD(self._client)
        self.datadome = Datadome(self._client)
        self.kasada = Kasada(self._client)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def get(self, *args, **kwargs):
        return await self._client.get(*args, **kwargs)

    async def post(self, *args, **kwargs):
        return await self._client.post(*args, **kwargs)

    @property
    def session(self):
        return self._client.session


__all__ = [
    'Salamoonder',
    'Client', 
    'Tasks',
    'AkamaiWeb',
    'AkamaiSBSD', 
    'Kasada',
    'Datadome',
    '__version__',
]