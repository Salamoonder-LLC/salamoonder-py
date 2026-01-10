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
        >>> captcha_url = datadome.parse_slider_url(
        ...     html=str,
        ...     datadome_cookie=str,
        ...     referer=str,
        ... )
    """
    
    def __init__(self, client: Client):
        self.client = client
 
    def parse_slider_url(self, html: str, datadome_cookie: str, referer: str):
        """Parse and construct DataDome slider captcha URL
        
        Extracts the DataDome JavaScript object from the HTML and constructs
        the device check URL for the slider captcha challenge.
        
        Args:
            html: Full HTML code.
            datadome_cookie: Current DD cookie.
            referer: The website you're trying to solve.
            
        Returns:
            str: Constructed slider URL
            
        Example:
            >>> url = datadome.parse_slider_url(
            ...     html=response.text,
            ...     datadome_cookie="ABC123...",
            ...     referer="https://example.com/page"
            ... )
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
            logger.error("IP is blocked (t=bv)")
            return None
        
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
        logger.info("Constructed slider URL: %s", captcha_url[:80] + "...")
        
        return captcha_url
    
    def parse_interstitial_url(self, html: str, datadome_cookie: str, referer: str):
        """Parse and construct DataDome interstitial challenge URL
        
        Extracts the DataDome JavaScript object from the HTML and constructs
        the device check URL for the interstitial challenge.
        
        Args:
            html: Full HTML code.
            datadome_cookie: Current DD cookie.
            referer: The website you're trying to solve.
            
        Returns:
            str: Constructed interstitial URL
            
        Example:
            >>> url = datadome.parse_interstitial_url(
            ...     html=response.text,
            ...     datadome_cookie="ABC123...",
            ...     referer="https://example.com/page"
            ... )
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
        logger.info("Constructed interstitial URL: %s", interstitial_url[:80] + "...")
        
        return interstitial_url