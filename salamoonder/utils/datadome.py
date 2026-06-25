import base64
import json
import re
import logging
from urllib.parse import urlencode, urlparse, urljoin
from salamoonder.client import Client

logger = logging.getLogger(__name__)


class Datadome:
    """Utility class for DataDome-related operations.
    
    Args:
        client: Initialized Client instance
        
    Example:
        >>> datadome = DataDomeUtils(client)
        >>> result = await datadome.get_slider_challenge(
        ...     html=str,
        ...     datadome_cookie=str,
        ...     referer=str,
        ... )
    """
    
    def __init__(self, client: Client):
        self.client = client
 
    async def get_slider_challenge(self, html: str, datadome_cookie: str, referer: str, proxy: str = None, headers: dict = None, user_agent: str = None):
        """Parse and construct DataDome slider captcha URL, then fetch the challenge page.

        Args:
            html: Full HTML code.
            datadome_cookie: Current DD cookie.
            referer: The website you're trying to solve.
            proxy: Optional proxy string.
            headers: Optional headers dict to send with the challenge request.
            user_agent: Optional User-Agent string (merged into headers, takes precedence).

        Returns:
            dict: ``{"captcha_url": str, "challenge_page": str}`` where
                  ``challenge_page`` is the response body encoded as base64.
        """
        logger.info("Parsing DataDome slider URL from HTML")

        try:
            js_object = html.split("var dd=")[1].split("</script>")[0]
            js_object = js_object.replace("'", '"')
            parsed = json.loads(js_object)
            logger.debug("Successfully parsed object")
        except Exception as e:
            logger.error("Failed to parse object: %s", e)
            raise RuntimeError("Failed to parse object.")

        if parsed.get("t") == "bv":
            logger.error("IP is blocked (t=bv), exiting...")
            exit(1)

        params = {
            "initialCid": parsed.get("cid"),
            "hash": parsed.get("hsh"),
            "cid": datadome_cookie,
            "t": parsed.get("t"),
            "referer": referer,
            "s": str(parsed.get("s")),
            "e": parsed.get("e"),
            "dm": "cd",
        }

        captcha_url = f"https://geo.captcha-delivery.com/captcha/?{urlencode(params)}"
        logger.info("Fetching slider challenge page: %s", captcha_url[:80] + "...")
        merged_headers = {**(headers or {})}

        if user_agent:
            merged_headers["User-Agent"] = user_agent

        response = await self.client.get(captcha_url, proxy=proxy, headers=merged_headers or None)

        return {
            "captcha_url": captcha_url,
            "challenge_page": base64.b64encode(response.content).decode("utf-8"),
        }
    
    async def get_interstitial_challenge(self, html: str, datadome_cookie: str, referer: str, proxy: str = None, headers: dict = None, user_agent: str = None):
        """Parse and construct DataDome interstitial challenge URL, then fetch the challenge page.

        Args:
            html: Full HTML code.
            datadome_cookie: Current DD cookie.
            referer: The website you're trying to solve.
            proxy: Optional proxy string.
            headers: Optional headers dict to send with the challenge request.
            user_agent: Optional User-Agent string (merged into headers, takes precedence).

        Returns:
            dict: ``{"captcha_url": str, "challenge_page": str}`` where
                  ``challenge_page`` is the response body encoded as base64.
        """
        logger.info("Parsing DataDome interstitial URL from HTML")

        try:
            js_object = html.split("var dd=")[1].split("</script>")[0]
            js_object = js_object.replace("'", '"')
            parsed = json.loads(js_object)
            logger.debug("Successfully parsed object")
        except Exception as e:
            logger.error("Failed to parse object: %s", e)
            raise RuntimeError("Failed to parse object.")

        params = {
            "initialCid": parsed.get("cid"),
            "hash": parsed.get("hsh"),
            "cid": datadome_cookie,
            "referer": referer,
            "s": str(parsed.get("s")),
            "e": str(parsed.get("e")),
            "b": str(parsed.get("b")),
            "dm": "cd",
        }

        interstitial_url = f"https://geo.captcha-delivery.com/interstitial/?{urlencode(params)}"
        logger.info("Fetching interstitial challenge page: %s", interstitial_url[:80] + "...")
        
        merged_headers = {**(headers or {})}

        if user_agent:
            merged_headers["User-Agent"] = user_agent

        response = await self.client.get(interstitial_url, proxy=proxy, headers=merged_headers or None)

        return {
            "captcha_url": interstitial_url,
            "challenge_page": base64.b64encode(response.content).decode("utf-8"),
        }