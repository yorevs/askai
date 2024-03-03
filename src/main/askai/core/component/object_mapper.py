"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: object_mapper.py
   @created: Fri, 28 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior"
      @site: https://github.com/yorevs/hspylib
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright·(c)·2024,·HSPyLib
"""
import inspect
import json
import logging as log
from inspect import isclass
from types import SimpleNamespace
from typing import Type, Callable, Dict, Optional, Any, TypeAlias

from hspylib.core.metaclass.singleton import Singleton

from askai.core.model.query_response import QueryResponse
from askai.exception.exceptions import InvalidMapping

FnConverter: TypeAlias = Callable[[Any, Type], Any]


class ObjectMapper(metaclass=Singleton):
    """Provide a utility class to convert one object into the other, and vice-versa."""

    INSTANCE: 'ObjectMapper' = None

    @staticmethod
    def _hash(type_from: Any, type_to: Type) -> str:
        """Create a hash value for both classes in a way that"""
        if isclass(type_from):
            return str(hash(type_from.__name__) + hash(type_to.__name__))
        else:
            return str(hash(type_from.__class__.__name__) + hash(type_to.__name__))

    @classmethod
    def _default_converter(cls, type1: Any, type2: Type) -> Any:
        """Default conversion function using the object variables. Attribute names must be equal in both classes."""
        return type2(**vars(type1))

    @classmethod
    def get_class_attributes(cls, clazz: Type):
        return [
            item[0] for item in inspect.getmembers(clazz)
            if not callable(getattr(clazz, item[0])) and not item[0].startswith('__')
        ]

    def __init__(self):
        self._converters: Dict[str, FnConverter] = {}

    def of_json(self, json_string: str, to_class: Type) -> Any:
        """"Convert a JSON string to an object on the provided type."""
        if not json_string:
            return ''
        ret_val = json_string
        try:
            json_obj = json.loads(json_string, object_hook=lambda d: SimpleNamespace(**d))
            ret_val = self.convert(json_obj, to_class)
        except ValueError as err:
            log.warning(f"Could not decode JSON string '%s' => %s", json_string, str(err))
        finally:
            return ret_val

    def convert(self, from_obj: Any, to_class: Type) -> Any:
        """Convert one object into another of the provided class type."""
        mapping_hash = self._hash(from_obj, to_class)
        try:
            fn_converter = self._get_converter(mapping_hash)
            obj = fn_converter(from_obj, to_class)
        except Exception as err:
            raise InvalidMapping(f"Can't convert {type(from_obj)} into {to_class}") from err
        return obj

    def register(self, type1: Any, type2: Any, fn_converter: FnConverter) -> None:
        """Register a new converter for the given types."""
        self._converters[self._hash(type1, type2)] = fn_converter

    def _get_converter(self, mapping_hash: str) -> Optional[FnConverter]:
        """Retrieve the converter for the provided the mapping hash."""
        return next((c for h, c in self._converters.items() if h == mapping_hash), self._default_converter)


assert ObjectMapper().INSTANCE is not None

if __name__ == '__main__':
    o = ObjectMapper.INSTANCE
    s = """
    {
        "query_type": "Type 1",
        "question": "list my downloads",
        "require_internet": false,
        "require_summarization": false,
        "require_command": true
    }
    """
    r = o.of_json(s, QueryResponse)
    print(r)
