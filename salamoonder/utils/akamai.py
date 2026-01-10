import base64
import json
import re
import logging
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from salamoonder.client import Client

logger = logging.getLogger(__name__)

class AkamaiWeb:
    """Utility class for Akamai-related operations.
    
    Args:
        client: Initialized Client instance
        
    Example:
        >>> akamai = Akamai(client)
        >>> data = akamai.fetch_and_extract(
        ...     website_url="https://example.com",
        ...     user_agent="Mozilla/5.0...",
        ...     proxy="http://proxy:8080"
        ... )
    """
    
    def __init__(self, client: Client):
        self.client = client
    
    def _extract_sec_ch_ua(self, user_agent: str):
        """Dynamically extract sec-ch-ua from user agent.
        
        Args:
            user_agent: Full user agent string
            
        Returns:
            str: sec-ch-ua header value
        """
        chrome_match = re.search(r'Chrome/(\d+)', user_agent)
        if chrome_match:
            version = chrome_match.group(1)
            return f'"Chromium";v="{version}", "Google Chrome";v="{version}", "Not?A_Brand";v="99"'
        
        return '"Chromium";v="122", "Google Chrome";v="122", "Not?A_Brand";v="99"'
    
    def _get_akamai_url(self, html: str, website_url: str):
        """Extract Akamai script URL from HTML.
        
        Args:
            html: HTML content to parse
            website_url: Base website URL
            
        Returns:
            tuple: (base_url, akamai_url) or (None, None) if not found
        """
        match = re.search(
            r'<script type="text/javascript".*?src="((/[0-9A-Za-z\-\_]+)+)">', 
            html
        )
        
        akamai_url_path = match.group(1) if match else None
        
        if not akamai_url_path:
            logger.warning("Failed to extract Akamai URL path from HTML")
            return None, None
        
        parsed_url = urlparse(website_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        akamai_url = urljoin(base_url, akamai_url_path)
        
        logger.debug("Extracted Akamai URL: %s", akamai_url)
        return base_url, akamai_url
    
    def fetch_and_extract(self, website_url: str, user_agent: str, proxy: str = None):
        """Comprehensive function to fetch and extract all Akamai data.
        
        This function handles the complete Akamai flow:
        1. Fetches the initial page to get _abck cookie and Akamai script URL
        2. Fetches the Akamai script to get bm_sz cookie
        3. Returns all relevant cookies and URLs
        
        Args:
            website_url: Target website URL
            user_agent: User agent string to use
            proxy: Optional proxy to use for requests
            
        Returns:
            dict: Dictionary containing:
                - base_url: Base URL of the website
                - akamai_url: Full URL to the Akamai script
                - script_data: The Akamai script content
                - abck: _abck cookie value
                - bm_sz: bm_sz cookie value
            
        Example:
            >>> data = akamai.fetch_and_extract(
            ...     website_url="https://example.com",
            ...     user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
            ...     proxy="http://proxy:8080"
            ... )
            >>> print(data['abck'], data['bm_sz'])
        """
        logger.info("Starting Akamai extraction for: %s", website_url)
        
        self.client.session.headers.clear()
        
        sec_user_agent = self._extract_sec_ch_ua(user_agent)
        logger.debug("Generated sec-ch-ua: %s", sec_user_agent)
        
        headers = {
            "sec-ch-ua": sec_user_agent,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": user_agent,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, i",
        }
        
        logger.info("Fetching initial page...")
        resp = self.client.get(website_url, headers=headers, proxy=proxy, verify=False, impersonate="chrome133a")
        
        if resp.status_code != 200:
            logger.error("Initial request failed with status %d: %s", resp.status_code, resp.text)
            return None
        
        base_url, akamai_url = self._get_akamai_url(resp.text, website_url)

        
        if not akamai_url:
            logger.error("Failed to parse Akamai URL from response")
            return None
        
        logger.info("Akamai URL: %s", akamai_url)
        
        abck = resp.cookies.get("_abck")
        if not abck:
            logger.error("_abck cookie not found in initial response")
            return None
        
        logger.debug("Found _abck cookie: %s...", abck[:50])
        
        headers["referer"] = website_url
        headers["origin"] = base_url
        headers["accept"] = "*/*"
        headers["sec-fetch-site"] = "same-origin"
        headers["sec-fetch-dest"] = "script"
        headers["sec-fetch-mode"] = "no-cors"
        del headers["upgrade-insecure-requests"]
        del headers["sec-fetch-user"]
        del headers["priority"]
        
        logger.info("Fetching Akamai script...")
        script_resp = self.client.get(akamai_url, headers=headers, proxy=proxy, verify=False, impersonate="chrome133a")
        
        if script_resp.status_code != 200:
            logger.error("Script fetch failed with status %d", script_resp.status_code)
            return None
        
        bm_sz = self.client.session.cookies.get("bm_sz")
        
        if not bm_sz:
            logger.error("bm_sz cookie not found")
            return None
        
        logger.info("Successfully extracted all Akamai data")
        logger.debug("bm_sz: %s", bm_sz)
        logger.debug("Script data length: %d bytes", len(script_resp.text))

        return {
            "base_url": base_url,
            "akamai_url": akamai_url,
            "script_data": script_resp.text,
            "abck": abck,
            "bm_sz": bm_sz,
        }
    
    def post_sensor(self, akamai_url: str, sensor_data: str, user_agent: str, 
                    website_url: str, proxy: str = None):
        """Post sensor data to Akamai endpoint and get updated _abck cookie.
        
        Args:
            akamai_url: The Akamai script URL (from fetch_and_extract)
            sensor_data: Single sensor data string to post
            user_agent: User agent string to use
            website_url: Original website URL (for referer/origin headers)
            proxy: Optional proxy to use for the request
            
        Returns:
            dict: Dictionary containing:
                - abck: Updated _abck cookie value
                - bm_sz: Updated bm_sz cookie value (if available)
                - cookies: All cookies from the response
                Or None if the request fails
                
        Example:
            >>> # First get initial data
            >>> data = akamai.fetch_and_extract(...)
            >>> 
            >>> # Then post sensor data one at a time
            >>> result1 = akamai.post_sensor(
            ...     akamai_url=data['akamai_url'],
            ...     sensor_data="sensor1_string",
            ...     user_agent="Mozilla/5.0...",
            ...     website_url="https://example.com",
            ...     proxy="http://proxy:8080"
            ... )
            >>> result2 = akamai.post_sensor(
            ...     akamai_url=data['akamai_url'],
            ...     sensor_data="sensor2_string",
            ...     user_agent="Mozilla/5.0...",
            ...     website_url="https://example.com"
            ... )
            >>> print(result2['abck'])
        """
        logger.info("Posting sensor data to Akamai endpoint")
        
        logger.debug("Current session cookies: %s", dict(self.client.session.cookies))
        
        sec_user_agent = self._extract_sec_ch_ua(user_agent)
        
        parsed_url = urlparse(website_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        headers = {
            "sec-ch-ua": sec_user_agent,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": user_agent,
            "content-type": "application/json",
            "accept": "*/*",
            "origin": base_url,
            "referer": website_url,
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "en-US,en;q=0.9",
        }
        
        payload = {'sensor_data': sensor_data}
        logger.debug("Posting sensor data, payload size: %d bytes", len(str(payload)))
        
        resp = self.client.post(
            url=akamai_url,
            headers=headers,
            json=payload,
            proxy=proxy,
            verify=False,
            impersonate="chrome133a"
        )
        
        logger.info("Sensor post response: status=%d", resp.status_code)
        
        if resp.status_code != 201:
            logger.error("Sensor post failed with status %d: %s", resp.status_code, resp.text[:200])
            try:
                json_resp = resp.json()
                if json_resp.get("success") == "false":
                    logger.error("Response indicates failure: %s", json_resp)
                    return None
            except:
                pass
            return None
        
        # Get updated cookies from response
        abck = resp.cookies.get("_abck")
        
        if not abck:
            logger.warning("No updated _abck cookie found in response")
            return None
        
        # Also check for updated bm_sz
        bm_sz = resp.cookies.get("bm_sz") or self.client.session.cookies.get("bm_sz")
        
        logger.info("Successfully posted sensor data and received updated _abck")
        logger.debug("Updated _abck: %s...", abck[:50])
        logger.debug("Session cookies after request: %s", dict(self.client.session.cookies))
        
        return {
            "_abck": abck,
            "bm_sz": bm_sz,
            "cookies": dict(self.client.session.cookies)
        }

class AkamaiSBSD:
    """Utility class for Akamai-related operations.
    
    Args:
        client: Initialized Client instance
    """
    
    def __init__(self, client: Client):
        self.client = client

    def _extract_sec_ch_ua(self, user_agent: str):
        """Dynamically extract sec-ch-ua from user agent.
        
        Args:
            user_agent: Full user agent string
            
        Returns:
            str: sec-ch-ua header value
        """
        chrome_match = re.search(r'Chrome/(\d+)', user_agent)
        if chrome_match:
            version = chrome_match.group(1)
            return f'"Chromium";v="{version}", "Google Chrome";v="{version}", "Not?A_Brand";v="99"'
        
        return '"Chromium";v="122", "Google Chrome";v="122", "Not?A_Brand";v="99"'
    
    def _get_sbsd_url(self, html: str, base_url: str) -> str | None:
        match = re.search(
            r'<script[^>]+src=["\']([^"\']*/\.well-known/sbsd/[^"\']+)["\']',
            html,
            re.IGNORECASE,
        )

        if not match:
            return None

        return urljoin(base_url, match.group(1))
    
    def fetch_and_extract(self, website_url: str, user_agent: str, proxy: str = None):
        logger.info("Starting SBSD extraction for: %s", website_url)

        self.client.session.headers.clear()

        sec_user_agent = self._extract_sec_ch_ua(user_agent)

        headers = {
            "sec-ch-ua": sec_user_agent,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": user_agent,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=0, i",
        }

        logger.info("Fetching initial page...")
        resp = self.client.get(
            website_url,
            headers=headers,
            proxy=proxy,
            verify=False,
            impersonate="chrome133a",
        )
        
        if resp.status_code != 200:
            logger.error("Initial request failed: %d", resp.status_code)
            return None

        parsed = urlparse(website_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        sbsd_url = self._get_sbsd_url(resp.text, base_url)
        if not sbsd_url:
            logger.error("Failed to parse SBSD URL")
            return None

        logger.info("SBSD URL: %s", sbsd_url)

        headers["referer"] = website_url
        headers["origin"] = base_url
        headers["accept"] = "*/*"
        headers["sec-fetch-site"] = "same-origin"
        headers["sec-fetch-dest"] = "script"
        headers["sec-fetch-mode"] = "no-cors"

        del headers["upgrade-insecure-requests"]
        del headers["sec-fetch-user"]
        del headers["priority"]

        logger.info("Fetching SBSD script...")
        script_resp = self.client.get(
            sbsd_url,
            headers=headers,
            proxy=proxy,
            verify=False,
            impersonate="chrome133a",
        )

        if script_resp.status_code != 200:
            logger.error("SBSD script fetch failed: %d", script_resp.status_code)
            return None

        cookies = self.client.session.cookies

        bm_so = cookies.get("bm_so")
        sbsd_o = cookies.get("sbsd_o")

        if bm_so:
            cookie_name = "bm_so"
            cookie_value = bm_so
        elif sbsd_o:
            cookie_name = "sbsd_o"
            cookie_value = sbsd_o
        else:
            logger.error("Neither bm_so nor sbsd_o cookie found")
            return None

        logger.info("Successfully extracted SBSD data")
        logger.debug("Using cookie: %s", cookie_name)
        logger.debug("Script data length: %d bytes", len(script_resp.text))

        return {
            "base_url": base_url,
            "sbsd_url": sbsd_url,
            "script_data": script_resp.text,
            "cookie_name": cookie_name,
            "cookie_value": cookie_value,
        }
    
    def post_sbsd(self, sbsd_payload: str, post_url: str, user_agent: str, website_url: str, proxy: str = None):
        """Post SBSD payload and return updated cookies"""

        logger.info("Posting SBSD payload")

        try:
            decoded = base64.b64decode(sbsd_payload).decode("utf-8")
        except Exception as e:
            logger.error("SBSD payload decode failed: %s", e)
            return None

        body = {
            "body": decoded
        }

        sec_ch_ua = self._extract_sec_ch_ua(user_agent)

        parsed = urlparse(website_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        headers = {
            "sec-ch-ua": sec_ch_ua,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "user-agent": user_agent,
            "content-type": "application/json",
            "accept": "*/*",
            "origin": base_url,
            "referer": website_url,
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-language": "en-US,en;q=0.9",
            "priority": "u=1, i",
        }

        logger.debug("SBSD post payload size: %d bytes", len(decoded))
        
        # Extract URL without query string
        parsed_post = urlparse(post_url)
        post_url = f"{parsed_post.scheme}://{parsed_post.netloc}{parsed_post.path}"
        logger.debug("SBSD post URL: %s", post_url)

        resp = self.client.post(
            url=post_url,
            headers=headers,
            json=body,
            proxy=proxy,
            verify=False,
            impersonate="chrome133a"
        )

        logger.info("SBSD response status: %d", resp.status_code)
        
        if resp.status_code != 200:
            logger.error("SBSD post failed: %s", resp.text[:200])
            return None

        cookies = dict(self.client.session.cookies)

        if not cookies:
            logger.warning("No cookies set after SBSD post")
            return None

        logger.info("SBSD post succeeded")
        logger.debug("Session cookies: %s", cookies)

        return {
            "cookies": cookies
        }