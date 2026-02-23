import base64
import json
import re
import logging
from urllib.parse import urlencode, urlparse, urljoin
from salamoonder.client import Client

logger = logging.getLogger(__name__)


class Kasada:
    """Utility class for Kasada bot detection extraction and payload solving.
    
    This class provides methods to extract Kasada protection scripts from blocked pages
    and post solved payloads to bypass the challenge.
    
    Args:
        client (Client): Initialized Client instance
        
    Example:
        >>> kasada = Kasada(client)
        >>> script_data = kasada.parse_kasada_script(
        ...     url="https://example.com/fp",
        ...     user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        ...     proxy="http://proxy:8080"
        ... )
        >>> payload_result = kasada.post_payload(
        ...     url="https://example.com",
        ...     solution=solved_data,
        ...     user_agent=user_agent,
        ...     proxy=proxy
        ... )
    """
    def __init__(self, client: Client):
        self.client = client
    
    def _extract_sec_ch_ua(self, user_agent: str):
        """Dynamically extract sec-ch-ua header value from user agent string.
        
        Parses the Chrome version from the User-Agent header and constructs
        the proper Sec-CH-UA value with all required brand information.
        If Chrome version cannot be extracted, defaults to Chrome 122.
        
        Args:
            user_agent (str): Full user agent string
                Example: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36... Chrome/122.0.0.0 Safari/537.36"
            
        Returns:
            str: Properly formatted sec-ch-ua header value
                Example: '"Chromium";v="122", "Google Chrome";v="122", "Not?A_Brand";v="99"'
                
        Example:
            >>> ua = "Mozilla/5.0 ... Chrome/144.0.0.0 Safari/537.36"
            >>> header = kasada._extract_sec_ch_ua(ua)
            >>> print(header)
            "Chromium";v="144", "Google Chrome";v="144", "Not?A_Brand";v="99"
        """
        chrome_match = re.search(r'Chrome/(\d+)', user_agent)
        if chrome_match:
            version = chrome_match.group(1)
            return f'"Chromium";v="{version}", "Google Chrome";v="{version}", "Not?A_Brand";v="99"'
        
        return '"Chromium";v="122", "Google Chrome";v="122", "Not?A_Brand";v="99"'

    def _get_script_url(self, html, base_url):
        """Parse the Kasada script from HTML response.
        
        Searches for the Kasada script, which can be either:
        1. Inline: JavaScript code embedded directly in <script> tags with identifiers like
           "KPSDK.scriptStart" or "ips.js"
        2. External: Referenced via <script src="..."> tags that need to be fetched
        
        The function prioritizes inline scripts and returns both found inline content
        and all external script URLs for further processing.
        
        Args:
            html (str): Full HTML source from the protected page response
            base_url (str): Base origin URL for resolving relative script paths
                Must include protocol and domain. 
                Example: "https://example.com" (not "https://example.com/path")
            
        Returns:
            dict: Script data with one of two structures:
            
                If inline script found:
                    {
                        "type": "inline",
                        "content": "<complete javascript code as string>"
                    }
                
                If only external scripts found:
                    {
                        "type": "external",
                        "urls": [
                            "https://example.com/scripts/ips.js",
                            "https://cdn.example.com/other.js"
                        ]
                    }
                    
        Example:
            >>> html_response = client.get(url).text
            >>> result = kasada._get_script_url(html_response, "https://kick.com")
            >>> if result["type"] == "inline":
            ...     print(f"Found inline script: {len(result['content'])} bytes")
            ... else:
            ...     print(f"Found {len(result['urls'])} external scripts")
        """
        external_scripts = re.findall(r'<script\s+src=["\']([^"\']+)["\']', html)
        inline_scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)

        logger.debug("Found %d external and %d inline scripts", len(external_scripts), len(inline_scripts))

        for inline in inline_scripts:
            if "KPSDK.scriptStart" in inline or "ips.js" in inline:
                logger.debug("Found inline Kasada script: %d bytes", len(inline))
                return { "type": "inline", "content": inline.strip() }

        script_urls = []
        for src in external_scripts:
            src = re.sub(r"&amp;", "&", src)

            if not src.startswith("http"):
                src = f"{base_url.rstrip('/')}/{src.lstrip('/')}"

            script_urls.append(src)

        logger.debug("Resolved %d external script URLs", len(script_urls))
        return { "type": "external", "urls": script_urls }
    
    def parse_kasada_script(self, url: str, user_agent: str, proxy: str = None):
        """Extract Kasada protection script from a blocked page.
        
        This method performs a complete Kasada script extraction workflow:
        1. Fetches the fingerprint endpoint (/fp) which returns a 429 status with HTML
        2. Parses the response to identify if Kasada is loaded inline or as external script
        3. For external scripts, fetches each URL to find the one containing Kasada logic
        4. Wraps the script with KPSDK initialization code
        5. Returns the complete script and its source URL
        
        Args:
            url (str): Target fingerprint endpoint URL
                Example: "https://example.com/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v=j-1.2.170"
            user_agent (str): User agent string to identify as
                Example: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"
            proxy (str, optional): HTTP/HTTPS proxy URL. Defaults to None.
                Example: "http://user:pass@proxy.com:8080"
            
        Returns:
            dict: Dictionary containing:
                - script (str): Complete Kasada script wrapped with KPSDK initialization
                - script_url (str): URL of the fetched external script, or empty string if inline
            Or None if the initial request doesn't return 429 status
            
        Note:
            The fingerprint endpoint is expected to return HTTP 429 (Too Many Requests)
            status code with HTML containing Kasada script references. A different status
            indicates the endpoint is not properly protected or the request failed.
            
        Example:
            >>> kasada = Kasada(client)
            >>> result = kasada.parse_kasada_script(
            ...     url="https://kick.com/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v=j-1.2.170",
            ...     user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
            ...     proxy="http://proxy:8080"
            ... )
            >>> if result:
            ...     print(f"Script length: {len(result['script'])} bytes")
            ...     if result['script_url']:
            ...         print(f"External script URL: {result['script_url']}")
            ...     else:
            ...         print("Using inline script")
        """
        logger.info("Starting Kasada script extraction for: %s", urlparse(url).netloc)

        parsed_url = urlparse(url)
        query_params = dict([param.split('=') for param in parsed_url.query.split('&') if '=' in param])
        
        if 'x-kpsdk-v' not in query_params:
            logger.warning("x-kpsdk-v parameter not found in URL")
            return None
            
        self.client.session.headers.clear()

        base_url = f"https://{urlparse(url).netloc}"
        fingerprint_url = f"{base_url}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v=j-1.2.170"

        headers = {
            "sec-ch-ua": self._extract_sec_ch_ua(user_agent),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": user_agent,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "navigate",
            "sec-fetch-dest": "iframe",
            "accept-language": "en-US,en;q=0.9",
            "referer": f"{base_url}/",
            "priority": "u=0, i",
        }

        logger.info("Fetching fingerprint endpoint...")
        resp = self.client.get(fingerprint_url, headers=headers, proxy=proxy, verify=False, impersonate="chrome133a")

        if resp.status_code != 429:
            logger.warning("Expected 429 status code, got %d", resp.status_code)
            return None
        
        script_data = self._get_script_url(resp.text, base_url)

        scripts_content = ""
        script_url = ""

        if script_data["type"] == "inline":
            scripts_content = script_data["content"]
            logger.info("Using inline Kasada script")
        else:
            logger.info("Fetching external Kasada script(s), %d URLs to check", len(script_data["urls"]))
            
            for idx, src in enumerate(script_data["urls"], 1):
                logger.debug("Fetching external script %d/%d: %s", idx, len(script_data["urls"]), src[:80])
                resp = self.client.get(src, headers=headers, proxy=proxy, verify=False, impersonate="chrome133a")
                
                if "ips.js" in resp.text or "KPSDK.scriptStart" in resp.text:
                    scripts_content = resp.text
                    script_url = resp.url
                    logger.info("Successfully fetched Kasada script from URL: %s", src[:80])
                    break

        logger.debug("Final script size: %d bytes", len(scripts_content))
        logger.info("Kasada extraction complete")

        return {
            "script_content": f"""window.KPSDK={{}};KPSDK.now=typeof performance!=='undefined'&&performance.now?performance.now.bind(performance):Date.now.bind(Date);KPSDK.start=KPSDK.now(); {scripts_content}""",
            "script_url": script_url
        }

    def post_payload(self, url: str, solution: dict, user_agent: str, proxy: str = None, mfc: bool = False):
        """Post solved Kasada payload to the challenge verification endpoint.
        
        This method sends the solved payload (from Salamoonder) back to Kasada's
        verification endpoint to complete the challenge and obtain valid session cookies.
        
        Args:
            url (str): Base website URL (not the /tl endpoint)
                Example: "https://example.com"
            solution (dict): Solved payload data containing:
                - headers (dict): x-kpsdk-* headers (x-kpsdk-ct, x-kpsdk-dt, x-kpsdk-im, x-kpsdk-v)
                - payload (str): Base64-encoded binary payload
            user_agent (str): User agent string to use for the request
            proxy (str, optional): HTTP/HTTPS proxy URL. Defaults to None.
            
        Returns:
            dict: Dictionary containing:
                - status_code (int): HTTP response status code
                - response_text (str): Response body content
                - cookies (dict): Any cookies received in response
                - headers (dict): Response headers
                - x-kpsdk-* headers: Extracted Kasada response headers (ct, r, st, v, h, fc)
            Or None if the POST request fails
            
        Note:
            The /tl endpoint is automatically constructed from the base URL using
            the standard Kasada path structure. The payload should be base64-decoded
            before sending as binary data.
            
        Example:
            >>> # Assuming solution obtained from solver service
            >>> solution = {
            ...     "headers": {
            ...         "x-kpsdk-v": "j-1.2.170",
            ...         "x-kpsdk-ct": "...",
            ...         "x-kpsdk-dt": "...",
            ...         "x-kpsdk-im": "..."
            ...     },
            ...     "payload": "base64_encoded_payload_data"
            ... }
            >>> result = kasada.post_payload(
            ...     url="https://example.com",
            ...     solution=solution,
            ...     user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            ...     proxy="http://proxy:8080"
            ... )
            >>> if result and result['status_code'] == 200:
            ...     print("Challenge solved successfully!")
        """
        logger.info("Starting Kasada payload post for: %s", urlparse(url).netloc)
        
        self.client.session.headers.clear()

        headers = {
            "Content-Type": "application/octet-stream",
            "upgrade-insecure-requests": "1",
            "user-agent": user_agent,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-ch-ua": self._extract_sec_ch_ua(user_agent),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-language": "en-US,en;q=0.9",
            "referer": f"https://{urlparse(url).netloc}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/fp?x-kpsdk-v={solution['headers']['x-kpsdk-v']}",
            "priority": "u=0, i",
            "x-kpsdk-ct": solution['headers']['x-kpsdk-ct'],
            "x-kpsdk-dt": solution['headers']['x-kpsdk-dt'],
            "x-kpsdk-im": solution['headers']['x-kpsdk-im'],
            "x-kpsdk-h": "01",
            "x-kpsdk-v": solution['headers']['x-kpsdk-v'],
        }

        pyld = base64.b64decode(solution['payload'])
        logger.debug("Payload size: %d bytes", len(pyld))

        logger.info("Posting payload to /tl endpoint...")
        resp = self.client.post(
            url=f"https://{urlparse(url).netloc}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/tl",
            headers=headers,
            data=pyld,
            proxy=proxy,
            verify=False,
            impersonate="chrome133a"
        )

        logger.info("Payload post response: status=%d", resp.status_code)

        if resp.status_code != 200:
            logger.warning("Unexpected response status: %d - %s", resp.status_code, resp.text[:200])

        mfc_response = None
        if mfc:
            mfc_response = self.client.get(f"https://{urlparse(url).netloc}/149e9513-01fa-4fb0-aad4-566afd725d1b/2d206a39-8ed7-437e-a3be-862e0f06eea3/mfc", headers=headers, proxy=proxy, verify=False, impersonate="chrome133a")

        return {
            "response": {
                "status_code": resp.status_code,
                "text": resp.text,
                "cookies": resp.cookies.get_dict(),
                "headers": {k: v for k, v in resp.headers.items()}
            },
            "x-kpsdk-ct": resp.headers['x-kpsdk-ct'] if 'x-kpsdk-ct' in resp.headers else None,
            "x-kpsdk-r": resp.headers['x-kpsdk-r'] if 'x-kpsdk-r' in resp.headers else None,
            "x-kpsdk-st": resp.headers['x-kpsdk-st'] if 'x-kpsdk-st' in resp.headers else None,
            "x-kpsdk-v": solution['headers']['x-kpsdk-v'] if 'x-kpsdk-v' in solution['headers'] else None,
            "x-kpsdk-h": mfc_response.headers['x-kpsdk-h'] if mfc_response and 'x-kpsdk-h' in mfc_response.headers else None,
            "x-kpsdk-fc": mfc_response.headers['x-kpsdk-fc'] if mfc_response and 'x-kpsdk-fc' in mfc_response.headers else None,
        }
