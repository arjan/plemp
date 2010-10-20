# Copyright 2010 Arjan Scherpenisse <arjan@scherpenisse.net>
# See LICENSE for details.

from twisted.internet import defer
from twisted.web import client

import flickrapi



class FlickrAPI (flickrapi.FlickrAPI):
    """
    Extends the flickrapi.FlickrAPI class to support twisted
    asynchronous HTTP requests.
    """

    def __flickr_call(self, **kwargs):
        '''Performs a Flickr API call with the given arguments. The method name
        itself should be passed as the 'method' parameter.
        
        Returns the unparsed data from Flickr::

        data = self.__flickr_call(method='flickr.photos.getInfo',
        photo_id='123', format='rest')
        '''
        if 'async' not in kwargs or not kwargs['async']:
            return flickrapi.FlickrAPI.__flickr_call(self, **kwargs)

        del kwargs['async']
        print "Calling %s" % kwargs

        post_data = self.encode_and_sign(kwargs)

        # Return value from cache if available
        if self.cache and self.cache.get(post_data):
            return defer.succeed(self.cache.get(post_data))

        url = "http://" + self.flickr_host + self.flickr_rest_form
        print url, post_data
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        d = client.getPage(url, method='POST', postdata=post_data, headers=headers)

        # Store in cache, if we have one
        if self.cache is not None:
            def setCache(reply):
                self.cache.set(post_data, reply)
                return reply
            d.addCallback(setCache)

        return d



    def __wrap_in_parser(self, wrapped_method, parse_format, *args, **kwargs):
        '''Wraps a method call in a parser.

        The parser will be looked up by the ``parse_format`` specifier. If there
        is a parser and ``kwargs['format']`` is set, it's set to ``rest``, and
        the response of the method is parsed before it's returned.
        '''

        # Find the parser, and set the format to rest if we're supposed to
        # parse it.
        if parse_format in flickrapi.rest_parsers and 'format' in kwargs:
            kwargs['format'] = 'rest'

        d = wrapped_method(*args, **kwargs)

        # Just return if we have no parser
        if parse_format not in flickrapi.rest_parsers:
            return d

        # Return the parsed data
        parser = flickrapi.rest_parsers[parse_format]
        if isinstance(d, defer.Deferred):
            d.addCallback(lambda data: parser(self, data))
            return d
        else:
            return parser(self, d)
