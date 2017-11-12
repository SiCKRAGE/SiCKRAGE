# -*- coding: utf-8 -*-
from babelfish import LanguageReverseConverter, language_converters


class SubsceneConverter(LanguageReverseConverter):
    def __init__(self):
        self.name_converter = language_converters['name']
        self.from_subscene = {
            'Farsi/Persian': ('fas',),
            'Brazillian Portuguese': ('por',),
        }
        self.to_subscene = {v: k for k, v in self.from_subscene.items()}
        self.codes = self.name_converter.codes | set(self.from_subscene.keys())

    def convert(self, alpha3, country=None, script=None):
        if (alpha3, country, script) in self.to_subscene:
            return self.to_subscene[(alpha3, country, script)]
        if (alpha3, country) in self.to_subscene:
            return self.to_subscene[(alpha3, country)]
        if (alpha3,) in self.to_subscene:
            return self.to_subscene[(alpha3,)]

        return self.name_converter.convert(alpha3, country, script)

    def reverse(self, subscene):
        if subscene in self.from_subscene:
            return self.from_subscene[subscene]

        return self.name_converter.reverse(subscene)
