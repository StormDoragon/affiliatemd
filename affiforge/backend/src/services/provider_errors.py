from fastapi import HTTPException


class IntegrationUnavailable(HTTPException):
    def __init__(self, provider: str):
        super().__init__(503, f"{provider} is not configured")


class IntegrationFailed(HTTPException):
    def __init__(self, provider: str):
        super().__init__(
            502, f"{provider} did not confirm the operation. Check the connection and try again."
        )
