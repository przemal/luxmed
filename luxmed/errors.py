from json.decoder import JSONDecodeError

from requests import Response


class LuxMedError(Exception):
    """Common base for all LUX MED errors."""
    CODES = set()

    def __init__(self, message: str, code: int = None):
        """Args:
            message (str): Human-readable message.
            code (int, optional): API error code.
        """
        self.message = message.rstrip('.')
        self.code = code
        full_message = self.message
        if code:
            full_message += f' (code {code})'
        super().__init__(full_message)

    @classmethod
    def from_response(cls, response: Response):
        """Returns first matched error based on the code present in the response.
        When no error matches, this class is returned.

        Args:
            response (Response): Raw JSON API response.

        Returns:
            LuxMedError: When nothing else matches.
            LuxMedAuthenticationError: When invalid credentials are being used for the API call.

        Raises:
            IndexError/KeyError: When response does not contain any errors.
        """
        try:
            errors = response.json()['Errors']
        except JSONDecodeError as error:
            raise cls('JSON data missing') from error

        code = errors[0]['ErrorCode']
        message = errors[0]['Message']
        for class_ in cls.__subclasses__():
            if code in class_.CODES:
                return class_(message, code=code)
        return cls(message, code=code)


class LuxMedConnectionError(LuxMedError):
    """Connection errors."""
    pass


class LuxMedTimeoutError(LuxMedError):
    """Timeout errors."""
    pass


class LuxMedAuthenticationError(LuxMedError):
    """Invalid credentials."""
    CODES = {2, }
