from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import inspect

from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx.util.nodes import nested_parse_with_titles

import trakt  # noqa: I902
from trakt import interfaces


def _get_methods(obj):
    for (name, _) in inspect.getmembers(obj, predicate=inspect.ismethod):
        if name.startswith('_'):
            continue

        yield '     * ' + name


def _format_apis(apis):

    output = []

    def make_path(path_dict, api_path):

        sorted_paths = collections.OrderedDict(
            sorted(path_dict.items()))
        for k, v in sorted_paths.items():
            if k is None:
                k = ''
            api_path.append(k)

            if isinstance(v, dict):
                api_path = make_path(v, api_path)
            else:
                api_ref = '     Interface Class: :py:class:`%s.%s`' % (
                    v.__module__, v.__class__.__name__)
                output.append(('``' + '/'.join(api_path) + '``',
                               api_ref,
                               list(_get_methods(v))))
                api_path.pop()
        else:
            if api_path:
                api_path.pop()

        return api_path

    make_path(apis, [])
    return output


class ListInterfacesDirective(rst.Directive):
    """Present a simple list of the plugins in a namespace."""

    option_spec = {
        'class': directives.class_option,
    }

    has_content = True

    def run(self):
        env = self.state.document.settings.env
        app = env.app

        iface_type = ' '.join(self.content).strip()
        app.info('documenting service interface %r' % iface_type)

        source_name = '<' + __name__ + '>'

        api_map = interfaces.construct_map(trakt.trakt.client)
        iface_map = {iface_type: api_map.get(iface_type)}

        result = ViewList()

        for api_path, api_ref, api_methods in _format_apis(iface_map):
            result.append(api_path, source_name)
            result.append('', source_name)
            result.append(api_ref, source_name)
            result.append('', source_name)

            for method in api_methods:
                result.append(method, source_name)
            result.append('', source_name)

        # Parse what we have into a new section.
        node = nodes.section()
        node.document = self.state.document
        nested_parse_with_titles(self.state, result, node)

        return node.children


def setup(app):
    app.info('loading trakt.sphinxext')
    app.add_directive('list-interfaces', ListInterfacesDirective)
