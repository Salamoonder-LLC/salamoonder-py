from curl_cffi import requests
import logging

logger = logging.getLogger(__name__)


class APIError(RuntimeError):
    """Raised when the API returns an error response."""
    pass


class MissingAPIKeyError(ValueError):
    """Raised when API key is missing or invalid."""
    pass


class Client:
    """HTTP client for Salamoonder API requests using curl_cffi.
    
    Args:
        api_key: Your Salamoonder API key
        base_url: API base URL (default: https://salamoonder.com/api)
        impersonate: Browser to impersonate (default: chrome133)
        
    Raises:
        MissingAPIKeyError: If api_key is empty or whitespace only
    """
    
    def __init__(self, api_key: str, base_url: str = "https://salamoonder.com/api", impersonate: str = "chrome133a"):
        if not api_key or not api_key.strip():
            logger.error("Attempted to initialize client without API key")
            raise MissingAPIKeyError(
                "API key is required. Pass it when creating the client."
            )

        self.api_key = api_key
        self.base_url = base_url
        self.impersonate = impersonate
        self.session = requests.Session()
        logger.debug("Client initialized with base_url: %s, impersonate: %s", base_url, impersonate)

    def _post(self, url: str, payload: dict, proxy: str = None):
        """Execute a POST request to the API.
        
        Args:
            url: Full URL endpoint
            payload: Request payload dictionary
            proxy: Optional proxy for this specific request
                   Format: "http://user:pass@host:port" or "socks5://host:port"
            
        Returns:
            dict: JSON response from the API
            
        Raises:
            MissingAPIKeyError: If API key is invalid
            APIError: If API returns an error or invalid response
        """
        if not self.api_key or not str(self.api_key).strip():
            logger.error("API key missing during request")
            raise MissingAPIKeyError("API key is required")

        body = {
            "api_key": self.api_key,
            **payload,
        }

        # Prepare request kwargs
        request_kwargs = {
            "json": body,
            "impersonate": self.impersonate
        }
        
        if proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}
            logger.debug("POST %s (via proxy: %s)", url, proxy)
        else:
            logger.debug("POST %s", url)
        
        resp = self.session.post(url, **request_kwargs)

        try:
            data = resp.json()
        except ValueError:
            logger.error("Invalid JSON response (status=%d)", resp.status_code)
            raise APIError(f"Invalid response from API ({resp.status_code})")

        if resp.status_code >= 400:
            msg = data.get("error_description") or data.get("error") or "Request failed"
            logger.error("API error (status=%d): %s", resp.status_code, msg)
            raise APIError(msg)

        logger.debug("Request successful (status=%d)", resp.status_code)
        return data
    
    def get(self, url: str, proxy: str = None, headers: dict = None, **kwargs):
        """Execute a GET request (helper for custom functions).
        
        Args:
            url: Full URL to fetch
            proxy: Optional proxy for this request
                   Format: "http://user:pass@host:port"
            headers: Optional headers dictionary
            **kwargs: Additional arguments to pass to requests.get (e.g., verify, timeout)
            
        Returns:
            Response: The curl_cffi response object
            
        Example:
            >>> response = client.get("https://example.com", proxy="http://proxy:8080")
        """
        request_kwargs = {
            "impersonate": self.impersonate
        }
        
        # Add any additional kwargs
        request_kwargs.update(kwargs)
        
        if headers:
            request_kwargs["headers"] = headers
            
        if proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}
            logger.debug("GET %s (via proxy: %s)", url, proxy)
        else:
            logger.debug("GET %s", url)
        
        return self.session.get(url, **request_kwargs)
    
    def post(self, url: str, proxy: str = None, headers: dict = None, data=None, json=None, **kwargs):
        """Execute a POST request (helper for custom functions).
        
        Args:
            url: Full URL to post to
            proxy: Optional proxy for this request
                   Format: "http://user:pass@host:port"
            headers: Optional headers dictionary
            data: Form data to send
            json: JSON data to send
            **kwargs: Additional arguments to pass to requests.post (e.g., verify, timeout)
            
        Returns:
            Response: The curl_cffi response object
            
        Example:
            >>> response = client.post(
            ...     "https://example.com/api",
            ...     json={"key": "value"},
            ...     proxy="http://proxy:8080"
            ... )
        """
        request_kwargs = {
            "impersonate": self.impersonate
        }
        
        # Add any additional kwargs
        request_kwargs.update(kwargs)
        
        if headers:
            request_kwargs["headers"] = headers
        if data:
            request_kwargs["data"] = data
        if json:
            request_kwargs["json"] = json
            
        if proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}
            logger.debug("POST %s (via proxy: %s)", url, proxy)
        else:
            logger.debug("POST %s", url)
        
        return self.session.post(url, **request_kwargs)