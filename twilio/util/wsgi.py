try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

from logging import getLogger
from urllib import quote
from urlparse import parse_qsl

from twilio.util import RequestValidator


class ValidateTwilioMiddleware(object):
  """
  WSGI middleware to validate that a request came from twilio.

  https://www.twilio.com/docs/security

  :param app:
    WSGI app to pass validated requests to.

  :param auth_token:
    Twilio Auth Token

  :param base_url:
    If passed use this as the URL to verify against instead of trying to
    reconstruct the URL.
  """
  def __init__(self, app, auth_token, callback_url=None):
    self.app = app
    self.callback_url = callback_url
    self.log = getLogger(self.__name__)
    self.validator = RequestValidator(auth_token)

  def __call__(self, environ, start_response):
    args = {}
    signature = environ.get('HTTP_X_TWILIO_SIGNATURE', None)
    url = self.build_request_url(environ)

    try:
      if environ['REQUEST_METHOD'] == 'POST':
        body = environ['wsgi.input'].read()
        environ['wsgi.input'] = StringIO(body)  # Make sure self.app can read this
        args = self.parse_query_string(body)

    except ValueError:
      self.log.error('We received POST input that was not FORM data.')
      return self.denied(start_response)

    if signature and self.validator.validate(url, args, signature):
      return self.app(environ, start_response)

    self.log.error('Could not validate twilio signature (%s) against URL %s with POST args: %s', signature, url, args)
    return self.denied(start_response)

  def build_request_url(self, environ):
    """
      Returns the original request URL, as close as we can get at least.

      :param baseurl:
        If provided, the URL which just needs the QUERY_STRING appended
    """
    if self.baseurl:
      url = [self.baseurl]

    else:
      url = [environ['wsgi.url_scheme'], '://']
      url.append(environ['HTTP_HOST'] or environ['SERVER_NAME'])

      if environ['wsgi.url_scheme'] == 'http' and environ['HTTP_PORT'] != 80:
        url.append(':' + environ['HTTP_PORT'])

      url.append(quote(environ.get('SCRIPT_NAME', '')))
      url.append(quote(environ.get('PATH_INFO', '')))

    if environ.get('QUERY_STRING'):
      url.append('?' + environ['QUERY_STRING'])

    return ''.join(url)

  def denied(self, start_response):
    headers = [('Content-type', 'text/plain')]
    start_response('400 Bad Request', headers)

    return "You're not Twilio!\n"

  def parse_query_string(self, query_string):
    params = {}

    for key, value in parse_qsl(query_string, keep_blank_values=True, strict_parsing=True):
      if key in params:
        raise ValueError('Duplicate POST parameter received from twilio!')

      params[key] = value[0]

    return params
