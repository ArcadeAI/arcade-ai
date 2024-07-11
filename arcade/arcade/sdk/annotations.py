from typing import _AnnotatedAlias, _tp_cache, _type_check


class BaseParamAnnotation:
    """Light base class wrapper for specific annotations"""

    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        raise TypeError("Type BaseParamAnnotation cannot be instantiated.")

    @_tp_cache
    def __class_getitem__(cls, params):
        msg = "BaseParamAnnotation[t, ...]: t must be a type."
        origin = _type_check(params[0], msg, allow_special_forms=True)
        metadata = tuple(params[1:])
        return _AnnotatedAlias(origin, metadata)


class Inferrable(BaseParamAnnotation):
    """An annotation for a parameter that can be inferred by a model."""

    pass


class Opaque(BaseParamAnnotation):
    """An annotation for a parameter that cannot be inferred by a model."""

    pass
