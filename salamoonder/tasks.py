import time
import logging
from salamoonder.client import Client, APIError

logger = logging.getLogger(__name__)


class Tasks:
    """Task management for Salamoonder captcha solving.
    
    Args:
        client: Initialized Client instance
    """
    
    def __init__(self, client):
        self.client = client
        self.create_url = "https://salamoonder.com/api/createTask"
        self.get_url = "https://salamoonder.com/api/getTaskResult"

    def createTask(self, task_type, **kwargs):
        """Create a new captcha solving task.
        
        Args:
            task_type: Type of task (e.g., "KasadaCaptchaSolver", "Twitch_PublicIntegrity")
            **kwargs: Task-specific parameters
            
        Supported task types:
            - KasadaCaptchaSolver: Requires pjs_url, optional cd_only
            - Twitch_PublicIntegrity: Requires access_token, proxy; optional device_id, client_id
            - IncapsulaReese84: Requires website, submit_payload
            - IncapsulaUTMVCSolver: Requires website
            
        Returns:
            str: Task ID for polling results
            
        Raises:
            APIError: If task creation fails
            
        Example:
            >>> task_id = tasks.createTask(
            ...     "KasadaCaptchaSolver",
            ...     pjs_url="https://example.com/pjs",
            ...     cd_only=False
            ... )
        """
        task = {"type": task_type}

        if task_type == "KasadaCaptchaSolver":
            task["pjs"] = kwargs.get("pjs_url")
            task["cdOnly"] = kwargs.get("cd_only")

        elif task_type == "Twitch_PublicIntegrity":
            task["access_token"] = kwargs.get("access_token")
            task["proxy"] = kwargs.get("proxy")
            if "device_id" in kwargs: 
                task["device_id"] = kwargs.get("device_id")
            if "client_id" in kwargs: 
                task["client_id"] = kwargs.get("client_id")

        elif task_type == "IncapsulaReese84Solver":
            task["type"] = "IncapsulaReese84Solver"
            task["website"] = kwargs.get("website")
            task["submit_payload"] = kwargs.get("submit_payload")

            if "user_agent" in kwargs:
                task['user_agent'] = kwargs.get("user_agent")

        elif task_type == "IncapsulaUTMVCSolver":
            task["type"] = "IncapsulaUTMVCSolver"
            task["website"] = kwargs.get("website")

            if "user_agent" in kwargs:
                task['user_agent'] = kwargs.get("user_agent")

        elif task_type == "AkamaiWebSensorSolver":
            task["type"] = "AkamaiWebSensorSolver"
            task["url"] = kwargs.get("url")
            task["abck"] = kwargs.get("abck")
            task["bmsz"] = kwargs.get("bmsz")
            task["script"] = kwargs.get("script")
            task["sensor_url"] = kwargs.get("sensor_url")
            task["count"] = kwargs.get("count")
            task["data"] = kwargs.get("data")
        
            if "user_agent" in kwargs:
                task['user_agent'] = kwargs.get("user_agent")

        elif task_type == "AkamaiSBSDSolver":
            task["type"] = "AkamaiSBSDSolver"
            task["url"] = kwargs.get("url")
            task["cookie"] = kwargs.get("cookie")
            task["sbsd_url"] = kwargs.get("sbsd_url")
            task["script"] = kwargs.get("script")

            if "user_agent" in kwargs:
                task['user_agent'] = kwargs.get("user_agent")

        elif task_type == "DataDomeSliderSolver":
            task["type"] = "DataDomeSliderSolver"
            task["captcha_url"] = kwargs.get("captcha_url")

            if "user_agent" in kwargs:
                task['user_agent'] = kwargs.get("user_agent")

            task["country_code"] = kwargs.get("country_code")

        elif task_type == "DataDomeInterstitialSolver":
            task["type"] = "DataDomeInterstitialSolver"
            task["captcha_url"] = kwargs.get("captcha_url")
            
            if "user_agent" in kwargs:
                task['user_agent'] = kwargs.get("user_agent")

            task["country_code"] = kwargs.get("country_code")

        logger.info("Creating task of type: %s", task_type)
        data = self.client._post(self.create_url, {"task": task})

        task_id = data.get("taskId")
        logger.info("Task created with ID: %s", task_id)

        return task_id

    def getTaskResult(self, task_id, interval=1):
        """Poll for task completion and retrieve results.
        
        Args:
            task_id: Task ID returned from createTask
            interval: Polling interval in seconds (default: 1)
            
        Returns:
            dict: Solution data when task is ready
            
        Raises:
            APIError: If task fails or returns unexpected status
            
        Example:
            >>> result = tasks.getTaskResult("task_123456")
        """
        logger.info("Polling task %s (interval=%ds)", task_id, interval)
        attempts = 0
        
        while True:
            attempts += 1
            data = self.client._post(self.get_url, {"taskId": task_id})

            status = data.get("status")
            logger.debug("Task %s status: %s (attempt %d)", task_id, status, attempts)
            
            if status == "PENDING":
                time.sleep(interval)
                continue

            if status == "ready":
                logger.info("Task %s completed after %d attempts", task_id, attempts)
                return data.get("solution")

            logger.error("Task %s failed with status: %s", task_id, status)
            raise APIError(f"Unexpected task status: {status}")