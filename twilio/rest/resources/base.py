import logging
from ...compat import urlparse

from .. import TwilioException
from .imports import parse_qs, json
from .util import transform_params, parse_rfc2822_date


class Resource(object):
    """A REST Resource"""

    name = "Resource"

    def __init__(self, base_uri, client):
        self.base_uri = base_uri
        self.client = client

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __hash__(self):
        return hash(frozenset(self.__dict__))

    def __ne__(self, other):
        return not self.__eq__(other)

    def request(self, method, uri, **kwargs):
        """
        Send an HTTP request to the resource.

        :raises: a :exc:`~twilio.TwilioRestException`
        """
        resp = self.client.make_twilio_request(method, uri, **kwargs)

        logging.debug(resp.content)

        if method == "DELETE":
            return resp, {}
        else:
            return resp, json.loads(resp.content)

    @property
    def uri(self):
        format = (self.base_uri, self.name)
        return "%s/%s" % format


class InstanceResource(Resource):
    """ The object representation of an instance response from the Twilio API

    :param parent: The parent list class for this instance resource.
        For example, the parent for a :class:`~twilio.rest.resources.Call`
        would be a :class:`~twilio.rest.resources.Calls` object.
    :type parent: :class:`~twilio.rest.resources.ListResource`
    :param str sid: The 34-character unique identifier for this instance
    """

    subresources = []
    id_key = "sid"

    def __init__(self, parent, sid):
        self.parent = parent
        self.name = sid
        super(InstanceResource, self).__init__(parent.uri, parent.client)

    def load(self, entries):
        if "from" in entries.keys():
            entries["from_"] = entries["from"]
            del entries["from"]

        if "uri" in entries.keys():
            del entries["uri"]

        for key in entries.keys():
            if key.startswith("date_") and isinstance(entries[key], str):
                entries[key] = parse_rfc2822_date(entries[key])

        self.__dict__.update(entries)

    def load_subresources(self):
        """
        Load all subresources
        """
        for resource in self.subresources:
            list_resource = resource(self.uri, self.client)
            self.__dict__[list_resource.key] = list_resource

    def update_instance(self, **kwargs):
        """ Make a POST request to the API to update an object's properties

        :return: None, this is purely side effecting
        :raises: a :class:`~twilio.rest.RestException` on failure
        """
        a = self.parent.update(self.name, **kwargs)
        self.load(a.__dict__)

    def delete_instance(self):
        """ Make a DELETE request to the API to delete the object

        :return: None, this is purely side effecting
        :raises: a :class:`~twilio.rest.RestException` on failure
        """
        return self.parent.delete(self.name)

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name[0:5])


class ListResource(Resource):

    name = "Resources"
    instance = InstanceResource

    def __init__(self, *args, **kwargs):
        super(ListResource, self).__init__(*args, **kwargs)

        try:
            self.key
        except AttributeError:
            self.key = self.name.lower()

    def get(self, sid):
        """ Get an instance resource by its sid

        Usage:

        .. code-block:: python

            message = client.messages.get("SM1234")
            print message.body

        :rtype: :class:`~twilio.rest.resources.InstanceResource`
        :raises: a :exc:`~twilio.TwilioRestException` if a resource with that
            sid does not exist, or the request fails
        """
        return self.get_instance(sid)

    def get_instance(self, sid):
        """Request the specified instance resource"""
        uri = "%s/%s" % (self.uri, sid)
        resp, item = self.request("GET", uri)
        return self.load_instance(item)

    def get_instances(self, params):
        """
        Query the list resource for a list of InstanceResources.

        Raises a :exc:`~twilio.TwilioRestException` if requesting a page of
        results that does not exist.

        :param dict params: List of URL parameters to be included in request
        :param int page: The page of results to retrieve (most recent at 0)
        :param int page_size: The number of results to be returned.

        :returns: -- the list of resources
        """
        params = transform_params(params)

        resp, page = self.request("GET", self.uri, params=params)

        if self.key not in page:
            raise TwilioException("Key %s not present in response" % self.key)

        return [self.load_instance(ir) for ir in page[self.key]]

    def create_instance(self, body):
        """
        Create an InstanceResource via a POST to the List Resource

        :param dict body: Dictionary of POST data
        """
        resp, instance = self.request("POST", self.uri,
                                      data=transform_params(body))

        #if resp.status_code not in (200, 201):
            #raise TwilioRestException(resp.status_code,
                                      #self.uri, "Resource not created")

        return self.load_instance(instance)

    def delete_instance(self, sid):
        """
        Delete an InstanceResource via DELETE

        body: string -- HTTP Body for the quest
        """
        uri = "%s/%s" % (self.uri, sid)
        resp, instance = self.request("DELETE", uri)
        return resp.status_code == 204

    def update_instance(self, sid, body):
        """
        Update an InstanceResource via a POST

        sid: string -- String identifier for the list resource
        body: dictionary -- Dict of items to POST
        """
        uri = "%s/%s" % (self.uri, sid)
        resp, entry = self.request("POST", uri, data=transform_params(body))
        return self.load_instance(entry)

    def count(self):
        """ .. deprecated:: 3.6.5

        Get the total number of instances for this resource

        Note: this query can be slow if you have many instances.

        :return: the total number of instances
        :rtype: int
        :raises: a :exc:`~twilio.TwilioRestException` if the request fails


        Example usage:

        .. code-block:: python

            print client.calls.count() # prints 323
        """
        # XXX: this should make a request with PageSize=1 to return as quickly
        # as possible
        resp, page = self.request("GET", self.uri)
        return page["total"]

    def iter(self, **kwargs):
        """ Return all instance resources using an iterator

        This will fetch a page of resources from the API and yield them in
        turn. When the page is exhausted, this will make a request to the API
        to retrieve the next page. Hence you may notice a pattern - the library
        will loop through 50 objects very quickly, but there will be a delay
        retrieving the 51st as the library must make another request to the API
        for resources.

        Example usage:

        .. code-block:: python

            for message in client.messages:
                print message.sid
        """
        params = transform_params(kwargs)

        while True:
            resp, page = self.request("GET", self.uri, params=params)

            if self.key not in page:
                raise StopIteration()

            for ir in page[self.key]:
                yield self.load_instance(ir)

            if not page.get('next_page_uri', ''):
                raise StopIteration()

            o = urlparse(page['next_page_uri'])
            params.update(parse_qs(o.query))

    def load_instance(self, data):
        instance = self.instance(self, data[self.instance.id_key])
        instance.load(data)
        instance.load_subresources()
        return instance

    def __str__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.count())

    def list(self, **kw):
        """Query the list resource for a list of InstanceResources.

        :param int page: The page of results to retrieve (most recent at 0)
        :param int page_size: The number of results to be returned.
        """
        return self.get_instances(kw)
