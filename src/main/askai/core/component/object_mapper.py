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
import json
from inspect import isclass
from types import SimpleNamespace
from typing import Type, Callable, Dict, Optional, Any, TypeAlias

from askai.exception.exceptions import InvalidMapping

FnConverter: TypeAlias = Callable[[Any, Type], Any]


class ObjectMapper:
    """TODO"""

    @staticmethod
    def _hash(type_from: Any, type_to: Type) -> str:
        """Create a hash value for both classes in a way that"""
        if isclass(type_from):
            return str(hash(type_from.__name__) + hash(type_to.__name__))
        else:
            return str(hash(type_from.__class__.__name__) + hash(type_to.__name__))

    @staticmethod
    def _default_converter(type1: Any, type2: Type) -> Any:
        """Default conversion function using the object variables. Attribute names must be equal in both classes."""
        return type2(**vars(type1))

    def __init__(self):
        self._converters: Dict[str, FnConverter] = {}

    def of_json(self, json_string: str, to_class: Type) -> Any:
        """"Convert a JSON string to an object on the provided type."""
        json_obj = json.loads(json_string, object_hook=lambda d: SimpleNamespace(**d))
        return self.convert(json_obj, to_class)

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
