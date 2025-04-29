class MetabaseRequestError(Exception):
    """Base exception for Metabase API request errors"""
    pass

class MetabaseConnectionError(MetabaseRequestError):
    """Exception raised when Metabase server is unreachable"""
    pass

class MetabaseResponseError(MetabaseRequestError):
    """Exception raised when Metabase returns a non-2xx status code"""
    def __init__(self, status, message, url):
        self.status = status
        self.message = message
        self.url = url
        super().__init__(f"Status {status}, message: '{message}', url: '{url}'")