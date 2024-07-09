# -*- coding: utf-8 -*-

from pydantic import BaseModel, ConfigDict, EmailStr, validate_email

# Custom validation error messages do not include the expected content of validation (i.e., input content). For supported expected content fields, refer to the following link:
# https://github.com/pydantic/pydantic-core/blob/a5cb7382643415b716b1a7a5392914e50f726528/tests/test_errors.py#L266
# For replacing expected content fields, refer to the following link:
# https://github.com/pydantic/pydantic/blob/caa78016433ec9b16a973f92f187a7b6bfde6cb5/docs/errors/errors.md?plain=1#L232
CUSTOM_VALIDATION_ERROR_MESSAGES = {
    'arguments_type': 'Incorrect argument type input',
    'assertion_error': 'Assertion execution error',
    'bool_parsing': 'Boolean value parsing error',
    'bool_type': 'Boolean type input error',
    'bytes_too_long': 'Byte length input too long',
    'bytes_too_short': 'Byte length input too short',
    'bytes_type': 'Byte type input error',
    'callable_type': 'Callable object type input error',
    'dataclass_exact_type': 'Dataclass instance type input error',
    'dataclass_type': 'Dataclass type input error',
    'date_from_datetime_inexact': 'Non-zero date component input',
    'date_from_datetime_parsing': 'Date input parsing error',
    'date_future': 'Date input is not in the future',
    'date_parsing': 'Date input validation error',
    'date_past': 'Date input is not in the past',
    'date_type': 'Date type input error',
    'datetime_future': 'Datetime input is not in the future',
    'datetime_object_invalid': 'Datetime input object invalid',
    'datetime_parsing': 'Datetime input parsing error',
    'datetime_past': 'Datetime input is not in the past',
    'datetime_type': 'Datetime type input error',
    'decimal_max_digits': 'Decimal input has too many digits',
    'decimal_max_places': 'Decimal places input error',
    'decimal_parsing': 'Decimal input parsing error',
    'decimal_type': 'Decimal type input error',
    'decimal_whole_digits': 'Decimal whole digits input error',
    'dict_type': 'Dictionary type input error',
    'enum': 'Enum member input error, allowed {expected}',
    'extra_forbidden': 'Extra fields input forbidden',
    'finite_number': 'Finite value input error',
    'float_parsing': 'Float parsing error',
    'float_type': 'Float type input error',
    'frozen_field': 'Frozen field input error',
    'frozen_instance': 'Modification of frozen instance forbidden',
    'frozen_set_type': 'Frozen set type input forbidden',
    'get_attribute_error': 'Attribute retrieval error',
    'greater_than': 'Input value too large',
    'greater_than_equal': 'Input value too large or equal',
    'int_from_float': 'Integer type input error',
    'int_parsing': 'Integer input parsing error',
    'int_parsing_size': 'Integer input parsing size error',
    'int_type': 'Integer type input error',
    'invalid_key': 'Invalid key input',
    'is_instance_of': 'Instance type input error',
    'is_subclass_of': 'Subclass type input error',
    'iterable_type': 'Iterable type input error',
    'iteration_error': 'Iteration value input error',
    'json_invalid': 'JSON string input error',
    'json_type': 'JSON type input error',
    'less_than': 'Input value too small',
    'less_than_equal': 'Input value too small or equal',
    'list_type': 'List type input error',
    'literal_error': 'Literal input error',
    'mapping_type': 'Mapping type input error',
    'missing': 'Missing required field',
    'missing_argument': 'Missing argument',
    'missing_keyword_only_argument': 'Missing keyword-only argument',
    'missing_positional_only_argument': 'Missing positional-only argument',
    'model_attributes_type': 'Model attributes type input error',
    'model_type': 'Model instance input error',
    'multiple_argument_values': 'Multiple argument values input',
    'multiple_of': 'Input value not a multiple',
    'no_such_attribute': 'Invalid attribute assignment',
    'none_required': 'Input value must be None',
    'recursion_loop': 'Recursion loop in input',
    'set_type': 'Set type input error',
    'string_pattern_mismatch': 'String pattern mismatch input',
    'string_sub_type': 'String subtype (non-strict instance) input error',
    'string_too_long': 'String input too long',
    'string_too_short': 'String input too short',
    'string_type': 'String type input error',
    'string_unicode': 'String input not Unicode',
    'time_delta_parsing': 'Time delta parsing error',
    'time_delta_type': 'Time delta type input error',
    'time_parsing': 'Time input parsing error',
    'time_type': 'Time type input error',
    'timezone_aware': 'Missing timezone input',
    'timezone_naive': 'Timezone input forbidden',
    'too_long': 'Input too long',
    'too_short': 'Input too short',
    'tuple_type': 'Tuple type input error',
    'unexpected_keyword_argument': 'Unexpected keyword argument input',
    'unexpected_positional_argument': 'Unexpected positional argument input',
    'union_tag_invalid': 'Union tag literal input error',
    'union_tag_not_found': 'Union tag argument not found',
    'url_parsing': 'URL input parsing error',
    'url_scheme': 'URL scheme input error',
    'url_syntax_violation': 'URL syntax violation',
    'url_too_long': 'URL input too long',
    'url_type': 'URL type input error',
    'uuid_parsing': 'UUID parsing error',
    'uuid_type': 'UUID type input error',
    'uuid_version': 'UUID version type input error',
    'value_error': 'Value input error',
}

CUSTOM_USAGE_ERROR_MESSAGES = {
    'class-not-fully-defined': 'Class attributes type not fully defined',
    'custom-json-schema': '__modify_schema__ method deprecated in V2',
    'decorator-missing-field': 'Invalid field validator defined',
    'discriminator-no-field': 'Discriminator field not fully defined',
    'discriminator-alias-type': 'Discriminator field defined using non-string type',
    'discriminator-needs-literal': 'Discriminator field requires literal definition',
    'discriminator-alias': 'Inconsistent discriminator field alias definition',
    'discriminator-validator': 'Field validator forbidden on discriminator field',
    'model-field-overridden': 'Typeless field override forbidden',
    'model-field-missing-annotation': 'Missing field type definition',
    'config-both': 'Duplicate configuration item defined',
    'removed-kwargs': 'Removed keyword configuration parameter called',
    'invalid-for-json-schema': 'Invalid JSON type present',
    'base-model-instantiated': 'Instantiation of base model forbidden',
    'undefined-annotation': 'Missing type definition',
    'schema-for-unknown-type': 'Unknown type definition',
    'create-model-field-definitions': 'Field definition error',
    'create-model-config-base': 'Configuration item definition error',
    'validator-no-fields': 'Field validator without specified fields',
    'validator-invalid-fields': 'Field validator fields definition error',
    'validator-instance-method': 'Field validator must be a class method',
    'model-serializer-instance-method': 'Serializer must be an instance method',
    'validator-v1-signature': 'V1 field validator error deprecated',
    'validator-signature': 'Field validator signature error',
    'field-serializer-signature': 'Field serializer signature unrecognized',
    'model-serializer-signature': 'Model serializer signature unrecognized',
    'multiple-field-serializers': 'Field serializers defined multiple times',
    'invalid_annotated_type': 'Invalid type definition',
    'type-adapter-config-unused': 'Type adapter configuration item definition error',
    'root-model-extra': 'Extra fields on root model forbidden',
}



class CustomEmailStr(EmailStr):
    @classmethod
    def _validate(cls, __input_value: str) -> str:
        return None if __input_value == '' else validate_email(__input_value)[1]


class SchemaBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)