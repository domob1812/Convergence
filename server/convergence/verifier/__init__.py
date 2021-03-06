#-*- coding: utf-8 -*-

# Copyright (c) 2011 Moxie Marlinspike
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#

from os.path import dirname, join


class OptionsError(Exception): pass

class Verifier(object):
    '''The base class for all verifier backends.'''


    #: Optional user-oriented textual description of backend
    #:  and backend-specific options_string allowed, for the CLI.
    description = None
    options_description = None

    def __init__(self, options_string=None):
        if options_string is not None:
            name = self.__class__.__name__
            raise OptionsError('This backend ({}) accepts no options.'.format(name))


    def verify(self, host, port, address, fingerprint, log):
        '''
        Verify whether are fingerprint is valid for a given target.

        This is an asynchronous call, and implementations return a Deferred
        object.  The callback is a (responseCode, fingerprintToCache) tuple,
        where fingerprintToCache can be None if the responseCode is 409 and
        the implementation does not know of any valid fingerprint.

        :Parameters:
        - `host` (str) - The target's host name.
        - `port` (int) - The target's port.
        - `address` (str or None) - The target's IP address to use, if provided.
        - `fingerprint` (str) - The fingerprint in question for this target.
        - `log` (Logger) - Logger to use for request-specific data.

        :Returns Type:
        Deferred
        '''
        raise NotImplementedError('Abstract method!')


    infonode_template = join(dirname(__file__), 'InfoNode.html')

    def getInfoNode(self, request):
        '''
        getDescription is called for GET requests.
        The purpose of this is to provide some information about the notary, if necessary.

        :Parameters:
        - `request` (twisted.web.server.Request) - GET request info object.

        :Returns Type:
        - String - Will be sent as an html response.
        - IRenderable - Will be rendered.
        - NOT_DONE_YET - For manual request.write(...)/finish() later.

        :Raises:
        - NotImplementedError - To serve generic info instead.
        '''

        try:
            from twisted.web.template import Element, renderer, XMLFile, XMLString
            from twisted.web.iweb import IRenderable
        except ImportError:
            try: return open(self.infonode_template).read()
            except (OSError, IOError): raise NotImplementedError()
        else:
            verifier = self

            def Verbatim(data):
                return Element(XMLString((
                    '<t:transparent xmlns:t="'
                        'http://twistedmatrix.com/ns/twisted.web.template/0.1">'
                    '{0}</t:transparent>' ).format(data) ))

            class Template(Element):
                loader = XMLFile(self.infonode_template)

                @renderer
                def description(self, request, tag):
                    html = verifier.getDescription()
                    if not IRenderable.providedBy(html): html = Verbatim(html)
                    return tag(html)

            return Template()


    #: HTML description to render for GET requests (using default canvas-template).
    html_description = None

    def getDescription(self):
        '''
        getDescription is called for GET requests.
        Should provide some dynamic information about the notary, if necessary.
        For static description text, just use html_description attribute.

        :Returns Type:
        - String - Will be rendered as notary description html.
        '''
        if self.html_description: return self.html_description
        description = '<p>Notary Type: {0}</p>'.format(self.__class__.__name__)
        if self.description:
            from twisted.web.server import escape
            description += '<pre>{}</pre>'.format(escape(self.description))
        return description


# Entry point modules must include "verifier" attribute with
#  backend implementation constructor (e.g. class) assigned to it
verifier = Verifier
