import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

def create_session(retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """Create a requests session with automatic retry logic."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_request(url: str, timeout: float = 15.0, stream: bool = False, headers: dict = None) -> requests.Response:
    """Perform a GET request using a session with retry logic."""
    session = create_session()
    # Add a user-agent to look like a standard browser request, which helps with GitHub and other APIs
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    if headers:
        default_headers.update(headers)
    return session.get(url, timeout=timeout, stream=stream, headers=default_headers)
