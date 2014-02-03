import os
import platform
import sys

import requests
from six import u

import twilio
from twilio import TwilioException
from twilio.rest.resources import Accounts
from twilio.rest.resources import Applications
from twilio.rest.resources import AuthorizedConnectApps
from twilio.rest.resources import CallerIds
from twilio.rest.resources import Calls
from twilio.rest.resources import Conferences
from twilio.rest.resources import ConnectApps
from twilio.rest.resources import MediaList
from twilio.rest.resources import Members
from twilio.rest.resources import Messages
from twilio.rest.resources import Notifications
from twilio.rest.resources import Participants
from twilio.rest.resources import PhoneNumbers
from twilio.rest.resources import Queues
from twilio.rest.resources import Recordings
from twilio.rest.resources import Sandboxes
from twilio.rest.resources import Sip
from twilio.rest.resources import Sms
from twilio.rest.resources import Transcriptions
from twilio.rest.resources import Usage


def find_credentials(environ=None):
    """
    Look in the current environment for Twilio credentials

    :param environ: the environment to check
    """
    environment = environ or os.environ
    try:
        account = environment["TWILIO_ACCOUNT_SID"]
        token = environment["TWILIO_AUTH_TOKEN"]
        return account, token
    except KeyError:
        return None, None


class Transport(object):
    """An object for codifying various parameters to send to the Twilio API.

    Example usage::

        from twilio.rest import Transport, TwilioRestClient
        transport = Transport(timeout=5)
        client = TwilioRestClient("AC123", "456", transport)

    :param float timeout: Raise an exception if the server has not issued a
        response for ``timeout`` seconds (more precisely, if no bytes have been
        received on the underlying socket for ``timeout`` seconds). The default
        is 30.1 is set so Twilio should always return an HTTP response within
        that time. Set a smaller timeout to return earlier.

    :param int retries: The number of times to retry failed requests to the
        Twilio API. A failed request is one that either:

        - raises a connection error or a connection timeout
        - receives a 429 Too Many Requests, a 502 Bad Gateway or a 503 Service
          Unavailable response on any HTTP method
        - receives a different status code in the 5xx status code range on a
          GET or DELETE request.

    :param str host: The host to authenticate against. Normally this is
        api.twilio.com, but could be a host for a proxy server.

    :param proxies: A dictionary of proxies to send the request through. This
        uses the same format as the `proxy logic in the Python Requests
        library.`
    :type proxies: dictionary or None
    """

    def __init__(self, timeout=30.1, retries=3, host="api.twilio.com",
                 proxies=None):
        # XXX: support a shorter connection timeout.
        self.timeout = timeout

        # XXX: this is currently ignored. Hoping to merge retry support into
        # urllib3, then we can call it directly there.
        self.retries = retries
        self.proxies = proxies

        self.host = host
        # We don't allow you to pass this in on purpose. Parts of the library
        # will probably break if you specify a different value here.
        self.version = "2010-04-01"


class TwilioRestClient(object):
    """
    A client for accessing the Twilio REST API

    :param str account: Your Account SID from `your dashboard
        <https://twilio.com/user/account>`_
    :param str token: Your Auth Token from `your dashboard
        <https://twilio.com/user/account>`_
    :param transport: A :class:`Transport` containing connection details about
        the HTTP requests you'd like to send to Twilio. Passing ``None`` will
        have the transport use Twilio's default settings.
    :type transport: :class:`Transport` or None
    """

    def __init__(self, account=None, token=None, transport=None):
        """
        Create a Twilio REST API client.
        """

        self.transport = transport or Transport()

        # Get account credentials
        if not account or not token:
            account, token = find_credentials()
            if not account or not token:
                raise TwilioException("""
Twilio could not find your account credentials. Pass them into the
TwilioRestClient constructor like this:

    client = TwilioRestClient(account='AC38135355602040856210245275870',
                              token='2flnf5tdp7so0lmfdu3d')

Or, add your credentials to your shell environment. From the terminal, run

    echo "export TWILIO_ACCOUNT_SID=AC3813535560204085626521" >> ~/.bashrc
    echo "export TWILIO_AUTH_TOKEN=2flnf5tdp7so0lmfdu3d7wod" >> ~/.bashrc

and be sure to replace the values for the Account SID and auth token with the
values from your Twilio Account at https://www.twilio.com/user/account.
""")

        # The HTTPS here is hard coded on purpose; you shouldn't be connecting
        # over HTTP with your auth credentials, as anyone with access to
        # the connection between your client and Twilio could steal your
        # credentials.
        self.base = "https://{host}".format(host=self.transport.host)
        auth = (account, token)
        version_uri = "{base}/{version}".format(base=self.base,
                                                version=self.transport.version)
        account_uri = "{base}/{version}/Accounts/{sid}".format(
            base=self.base, version=self.transport.version, sid=account)

        self.accounts = Accounts(version_uri, self)
        self.applications = Applications(account_uri, self)
        self.authorized_connect_apps = AuthorizedConnectApps(account_uri, self)
        self.calls = Calls(account_uri, self)
        self.caller_ids = CallerIds(account_uri, self)
        self.connect_apps = ConnectApps(account_uri, self)
        self.notifications = Notifications(account_uri, self)
        self.recordings = Recordings(account_uri, self)
        self.transcriptions = Transcriptions(account_uri, self)
        self.sms = Sms(account_uri, self)
        self.phone_numbers = PhoneNumbers(account_uri, self)
        self.conferences = Conferences(account_uri, self)
        self.queues = Queues(account_uri, self)
        self.sandboxes = Sandboxes(account_uri, self)
        self.usage = Usage(account_uri, self)
        self.messages = Messages(account_uri, self)
        self.media = MediaList(account_uri, self)
        self.sip = Sip(account_uri, self)

        self.auth = auth
        self.account_uri = account_uri

    def participants(self, conference_sid):
        """
        Return a :class:`~twilio.rest.resources.Participants` instance for the
        :class:`~twilio.rest.resources.Conference` with given conference_sid
        """
        base_uri = "%s/Conferences/%s" % (self.account_uri, conference_sid)
        return Participants(base_uri, self)

    def members(self, queue_sid):
        """
        Return a :class:`Members <twilio.rest.resources.Members>` instance for
        the :class:`Queue <twilio.rest.resources.Queue>` with the
        given queue_sid
        """
        base_uri = "%s/Queues/%s" % (self.account_uri, queue_sid)
        return Members(base_uri, self)

    def make_twilio_request(self, method, uri, **kwargs):
        """
        Make a request to Twilio. Throws an error

        :param string method: the HTTP method to use for the request
        :param string uri: the URI to request
        :param dict params: the query parameters to attach to the request
        :param dict data: the POST form data to send with the request

        :return: a response
        :rtype: :class:`requests.Response`
        :raises TwilioRestException: if the response is a 400
            or 500-level response
        :raises TwilioRequestException: if a response was not received; most
            likely a timeout, but possibly a connection error.
        """
        user_agent = "twilio-python/%s (Python %s)" % (
            twilio.__version__,
            platform.python_version(),
        )
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
        }

        if method == "POST" and "Content-Type" not in headers:
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        uri += ".json"

        try:
            resp = requests.request(method, uri, auth=self.auth,
                                    headers=headers,
                                    timeout=self.transport.timeout,
                                    proxies=self.transport.proxies, **kwargs)
        except requests.RequestException as e:
            raise TwilioRequestException(e)

        if not resp.ok:
            try:
                error = resp.json()
                code = error["code"]
                message = "%s: %s" % (code, error["message"])
            except Exception:
                code = None
                message = resp.content

            raise TwilioRestException(method, resp.url, resp.status_code, code,
                                      message)

        return resp


class TwilioRequestException(TwilioException):
    """ An exception raised when we don't get a HTTP response from the server

    :param Exception reason: The wrapped exception. see requests/exceptions.py
        for more information.
    :param str url: the requested URL that raised an exception.
    """
    def __init__(self, url, reason):
        self.reason = reason
        message = ("Exception caused when requesting url: "
                   "{url} (Caused by {typ}: {e})".format(
                       url=url, typ=type(reason), e=reason))
        TwilioException.__init__(self, message)


class TwilioRestException(TwilioException):
    """ A generic 400 or 500 level exception from the Twilio API

    :param str method: the HTTP method that was returned for the exception
    :param str uri: The URI that caused the exception
    :param int status: the HTTP status that was returned for the exception
    :param str msg: A human-readable message for the error
    :param int|None code: A Twilio-specific error code for the error. This is
         not available for all errors.
    """

    # XXX: Move this to the twilio.rest folder

    def __init__(self, method='GET', uri='/', status=200, code=None, msg=""):
        self.uri = uri
        self.status = status
        self.msg = msg
        self.code = code
        self.method = method

    def __str__(self):
        """ Try to pretty-print the exception, if this is going on screen. """

        def red(words):
            return u("\033[31m\033[49m%s\033[0m") % words

        def white(words):
            return u("\033[37m\033[49m%s\033[0m") % words

        def blue(words):
            return u("\033[34m\033[49m%s\033[0m") % words

        def teal(words):
            return u("\033[36m\033[49m%s\033[0m") % words

        def get_uri(code):
            return "https://www.twilio.com/docs/errors/{}".format(code)

        # If it makes sense to print a human readable error message, try to
        # do it. The one problem is that someone might catch this error and
        # try to display the message from it to an end user.
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            msg = (
                "\n{red_error} {request_was}\n\n{http_line}"
                "\n\n{twilio_returned}\n\n{message}\n".format(
                    red_error=red("HTTP Error"),
                    request_was=white("Your request was:"),
                    http_line=teal("%s %s" % (self.method, self.uri)),
                    twilio_returned=white(
                        "Twilio returned the following information:"),
                    message=blue(str(self.msg))
                ))
            if self.code:
                msg = "".join([msg, "\n{more_info}\n\n{uri}\n\n".format(
                    more_info=white("More information may be available here:"),
                    uri=blue(get_uri(self.code))),
                ])
            return msg
        else:
            return "HTTP {} error: {}".format(self.status, self.msg,
                                              self.uri)
