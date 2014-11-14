"""
Exceptions and their handlers.

Left over from Ruby client:
  class FolderExpected < StandardError; end
  class BadRequest < EgnyteError; end
  class DuplicateRecordExists < EgnyteError; end
  class MissingAttribute < EgnyteError; end

"""

from six.moves import http_client


class EgnyteError(Exception):
    """Base class for Egnyte SDK exceptions"""


class InvalidParameters(EgnyteError):
    """Invalid parameters were passed to an API request"""


class InsufficientPermissions(EgnyteError):
    """User does not have sufficient permissions to perform this action"""


class NotFound(EgnyteError):
    """Resource with name does not exist"""


class NotAuthorized(EgnyteError):
    """Access token is required"""


class JsonParseError(EgnyteError):
    """Response from the server could not be parsed properly"""


class DomainRequired(EgnyteError):
    """Domain name is required"""


class ClientIdRequired(EgnyteError):
    """Client id is required"""


class OAuthUsernameRequired(EgnyteError):
    """Username is required for OAuth authentication"""


class OAuthPasswordRequired(EgnyteError):
    """Password is required for OAuth authentication"""


class UnsupportedAuthStrategy(EgnyteError):
    """This OAuth flow is not supported by this API key"""


class RequestError(EgnyteError):
    """Other kinds of request errors"""


class FileExpected(EgnyteError):
    """
    """


class DuplicateRecordExists(EgnyteError):
    """Existing entity conflict"""


class FileSizeExceedsLimit(EgnyteError):
    """File is too large for this operation."""


def extract_errors(data):
    """
    Try to extract useful information from inconsistent error data structures.
    """
    if 'errors' in data:
        data = data['errors']
    if 'inputErrors' in data:
        for err in extract_errors(data['inputErrors']):
            yield err
    elif hasattr(data, 'keys'):
        if 'code' in data:
            yield data
        else:
            for value in data.values():
                for err in extract_errors(value):
                    yield err
    elif isinstance(data, list):
        for value in data:
            for err in extract_errors(value):
                yield err
    else:
        yield data


class ErrorMapping(dict):
    """Maps HTTP status to EgnyteError subclasses"""

    def __init__(self, values=None, ok_statuses=(http_client.OK, )):
        super(ErrorMapping, self).__init__({
            http_client.BAD_REQUEST: RequestError,
            http_client.UNAUTHORIZED: NotAuthorized,
            http_client.FORBIDDEN: InsufficientPermissions,
            http_client.NOT_FOUND: NotFound,
            http_client.CONFLICT: DuplicateRecordExists,
            http_client.REQUEST_ENTITY_TOO_LARGE: FileSizeExceedsLimit,
        })
        if values:
            self.update(values)
        self.ok_statuses = ok_statuses

    def map_error(self, response):
        return self.get(response.status_code, RequestError)

    def check_response(self, response, *ok_statuses):
        """
        Check if HTTP response has a correct status,
        try to raise a specific EgnyteError subclass if not
        """
        if not len(ok_statuses):
            ok_statuses = self.ok_statuses
        if response.status_code not in ok_statuses:
            errors = []
            error_type = self.map_error(response)
            try:
                data = response.json()
                for err in extract_errors(data):
                    errors.append(err)
            except Exception:
                errors.append({"http response": response.text})
            errors.append({"http status": response.status_code})
            raise error_type(*errors)
        return response

    def check_json_response(self, response, *ok_statuses):
        """
        Check if HTTP response has a correct status and then parse it as JSON,
        try to raise a specific EgnyteError subclass if not
        """
        try:
            return self.check_response(response, *ok_statuses).json()
        except ValueError:
            raise JsonParseError({"http response": response.text})

    def copy(self):
        """Make a copy preserving class of self"""
        return self.__class__(self)

default = ErrorMapping()
created = ErrorMapping(ok_statuses=(http_client.CREATED,))
