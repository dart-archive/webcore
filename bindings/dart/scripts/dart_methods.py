# Copyright (C) 2013 Google Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Generate template values for methods.

Extends IdlType and IdlUnionType with property |union_arguments|.

Design doc: http://www.chromium.org/developers/design-documents/idl-compiler
"""

from idl_types import IdlType, IdlUnionType, inherits_interface
import dart_types
from dart_utilities import DartUtilities
from v8_globals import includes


def generate_method(interface, method):
    arguments = method.arguments
    extended_attributes = method.extended_attributes
    idl_type = method.idl_type
    is_static = method.is_static
    name = method.name

    idl_type.add_includes_for_type()
    this_cpp_value = cpp_value(interface, method, len(arguments))

    def function_template():
        if is_static:
            return 'functionTemplate'
        if 'Unforgeable' in extended_attributes:
            return 'instanceTemplate'
        return 'prototypeTemplate'

    is_call_with_script_arguments = DartUtilities.has_extended_attribute_value(method, 'CallWith', 'ScriptArguments')
    if is_call_with_script_arguments:
        includes.update(['bindings/v8/ScriptCallStackFactory.h',
                         'core/inspector/ScriptArguments.h'])
    is_call_with_script_state = DartUtilities.has_extended_attribute_value(method, 'CallWith', 'ScriptState')
    if is_call_with_script_state:
        includes.add('bindings/dart/DartScriptState.h')
    is_check_security_for_node = 'CheckSecurity' in extended_attributes
    if is_check_security_for_node:
        includes.add('bindings/common/BindingSecurity.h')
    is_custom_element_callbacks = 'CustomElementCallbacks' in extended_attributes
    if is_custom_element_callbacks:
        includes.add('core/dom/custom/CustomElementCallbackDispatcher.h')

    has_event_listener_argument = any(
        argument for argument in arguments
        if argument.idl_type.name == 'EventListener')
    is_check_security_for_frame = (
        'CheckSecurity' in interface.extended_attributes and
        'DoNotCheckSecurity' not in extended_attributes)
    is_raises_exception = 'RaisesException' in extended_attributes

    if idl_type.union_arguments and len(idl_type.union_arguments) > 0:
        this_cpp_type = []
        for cpp_type in idl_type.member_types:
            this_cpp_type.append("RefPtr<%s>" % cpp_type)
    else:
        this_cpp_type = idl_type.cpp_type

    is_auto_scope = not 'DartNoAutoScope' in extended_attributes

    number_of_arguments = len(arguments)

    number_of_required_arguments = \
        len([
            argument for argument in arguments
            if not ((argument.is_optional and not ('Default' in argument.extended_attributes or argument.default_value)) or
                    argument.is_variadic)])

    arguments_data = [generate_argument(interface, method, argument, index)
                      for index, argument in enumerate(arguments)]

    is_custom = 'Custom' in extended_attributes or 'DartCustom' in extended_attributes

    method_data = {
        'activity_logging_world_list': DartUtilities.activity_logging_world_list(method),  # [ActivityLogging]
        'arguments': arguments_data,
        'conditional_string': DartUtilities.conditional_string(method),
        'cpp_type': this_cpp_type,
        'cpp_value': this_cpp_value,
        'dart_name': extended_attributes.get('DartName'),
        'deprecate_as': DartUtilities.deprecate_as(method),  # [DeprecateAs]
        'do_not_check_signature': not(is_static or
            DartUtilities.has_extended_attribute(method,
                ['DoNotCheckSecurity', 'DoNotCheckSignature', 'NotEnumerable',
                 'ReadOnly', 'RuntimeEnabled', 'Unforgeable'])),
        'function_template': function_template(),
        'idl_type': idl_type.base_type,
        'has_event_listener_argument': has_event_listener_argument,
        'has_exception_state':
            has_event_listener_argument or
            is_raises_exception or
            is_check_security_for_frame or
            any(argument for argument in arguments
                if argument.idl_type.name == 'SerializedScriptValue' or
                   argument.idl_type.is_integer_type),
        'is_auto_scope': is_auto_scope,
        'auto_scope': DartUtilities.bool_to_cpp(is_auto_scope),
        'is_call_with_execution_context': DartUtilities.has_extended_attribute_value(method, 'CallWith', 'ExecutionContext'),
        'is_call_with_script_arguments': is_call_with_script_arguments,
        'is_call_with_script_state': is_call_with_script_state,
        'is_check_security_for_frame': is_check_security_for_frame,
        'is_check_security_for_node': is_check_security_for_node,
        'is_custom': is_custom,
        'is_custom_dart': 'DartCustom' in extended_attributes,
        'is_custom_dart_new': DartUtilities.has_extended_attribute_value(method, 'DartCustom', 'New'),
        'is_custom_element_callbacks': is_custom_element_callbacks,
        'is_do_not_check_security': 'DoNotCheckSecurity' in extended_attributes,
        'is_do_not_check_signature': 'DoNotCheckSignature' in extended_attributes,
        'is_partial_interface_member': 'PartialInterfaceImplementedAs' in extended_attributes,
        'is_per_world_bindings': 'PerWorldBindings' in extended_attributes,
        'is_raises_exception': is_raises_exception,
        'is_read_only': 'ReadOnly' in extended_attributes,
        'is_static': is_static,
        # FIXME(terry): DartStrictTypeChecking no longer supported; TypeChecking is
        #               new extended attribute.
        'is_strict_type_checking':
            'DartStrictTypeChecking' in extended_attributes or
            'DartStrictTypeChecking' in interface.extended_attributes,
        'is_variadic': arguments and arguments[-1].is_variadic,
        'measure_as': DartUtilities.measure_as(method),  # [MeasureAs]
        'name': name,
        'number_of_arguments': number_of_arguments,
        'number_of_required_arguments': number_of_required_arguments,
        'number_of_required_or_variadic_arguments': len([
            argument for argument in arguments
            if not argument.is_optional]),
        'per_context_enabled_function': DartUtilities.per_context_enabled_function_name(method),  # [PerContextEnabled]
        'property_attributes': property_attributes(method),
        'runtime_enabled_function': DartUtilities.runtime_enabled_function_name(method),  # [RuntimeEnabled]
        'signature': 'v8::Local<v8::Signature>()' if is_static or 'DoNotCheckSignature' in extended_attributes else 'defaultSignature',
        'suppressed': (arguments and arguments[-1].is_variadic),  # FIXME: implement variadic
        'union_arguments': idl_type.union_arguments,
        'dart_set_return_value': dart_set_return_value(interface.name, method, this_cpp_value),
        'world_suffixes': ['', 'ForMainWorld'] if 'PerWorldBindings' in extended_attributes else [''],  # [PerWorldBindings]
    }
    return method_data


def generate_argument(interface, method, argument, index):
    extended_attributes = argument.extended_attributes
    idl_type = argument.idl_type
    this_cpp_value = cpp_value(interface, method, index)
    is_variadic_wrapper_type = argument.is_variadic and idl_type.is_wrapper_type
    use_heap_vector_type = is_variadic_wrapper_type and idl_type.is_will_be_garbage_collected
    auto_scope = not 'DartNoAutoScope' in extended_attributes
    this_has_default = 'Default' in extended_attributes
    arg_index = index + 1 if not method.is_static else index
    preprocessed_type = str(idl_type.preprocessed_type)
    # FIXMEDART: handle the drift between preprocessed type names in 1847 and
    # 1985 dartium builds in a more generic way.
    if preprocessed_type == 'unrestricted float':
        preprocessed_type = 'float'
    if preprocessed_type == 'unrestricted double':
        preprocessed_type = 'double'
    argument_data = {
        'cpp_type': idl_type.cpp_type_args(used_in_cpp_sequence=use_heap_vector_type),
        'cpp_value': this_cpp_value,
        'local_cpp_type': idl_type.cpp_type_args(argument.extended_attributes, used_as_argument=True),
        # FIXME: check that the default value's type is compatible with the argument's
        'default_value': str(argument.default_value) if argument.default_value else None,
        'enum_validation_expression': idl_type.enum_validation_expression,
        # Ignore 'Default' in extended_attributes not exposed in dart:html.
        'has_default': False,
        'has_event_listener_argument': any(
            argument_so_far for argument_so_far in method.arguments[:index]
            if argument_so_far.idl_type.name == 'EventListener'),
        'idl_type_object': idl_type,
        'preprocessed_type': preprocessed_type,
        # Dictionary is special-cased, but arrays and sequences shouldn't be
        'idl_type': not idl_type.array_or_sequence_type and idl_type.base_type,
        'index': index,
        'is_array_or_sequence_type': not not idl_type.array_or_sequence_type,
        'is_clamp': 'Clamp' in extended_attributes,
        'is_callback_interface': idl_type.is_callback_interface,
        'is_nullable': idl_type.is_nullable,
        # Only expose as optional if no default value.
        'is_optional': argument.is_optional and not (this_has_default or argument.default_value),
        'is_strict_type_checking': 'DartStrictTypeChecking' in extended_attributes,
        'is_variadic_wrapper_type': is_variadic_wrapper_type,
        'vector_type': 'WillBeHeapVector' if use_heap_vector_type else 'Vector',
        'is_wrapper_type': idl_type.is_wrapper_type,
        'name': argument.name,
        'dart_set_return_value_for_main_world': dart_set_return_value(interface.name, method, this_cpp_value, for_main_world=True),
        'dart_set_return_value': dart_set_return_value(interface.name, method, this_cpp_value),
        'arg_index': arg_index,
        'dart_value_to_local_cpp_value': dart_value_to_local_cpp_value(interface, argument, arg_index, auto_scope),
    }
    return argument_data


################################################################################
# Value handling
################################################################################

def cpp_value(interface, method, number_of_arguments):
    def cpp_argument(argument):
        argument_name = dart_types.check_reserved_name(argument.name)
        idl_type = argument.idl_type

        if idl_type.is_typed_array_type:
            return '%s.get()' % argument_name

        if idl_type.name == 'EventListener':
            if (interface.name == 'EventTarget' and
                method.name == 'removeEventListener'):
                # FIXME: remove this special case by moving get() into
                # EventTarget::removeEventListener
                return '%s.get()' % argument_name
            return argument.name
        if (idl_type.is_callback_interface or
            idl_type.name in ['NodeFilter', 'XPathNSResolver']):
            # FIXME: remove this special case
            return '%s.release()' % argument_name
        return argument_name

    # Truncate omitted optional arguments
    arguments = method.arguments[:number_of_arguments]
    cpp_arguments = DartUtilities.call_with_arguments(method)
    if ('PartialInterfaceImplementedAs' in method.extended_attributes and not method.is_static):
        cpp_arguments.append('*receiver')

    cpp_arguments.extend(cpp_argument(argument) for argument in arguments)
    this_union_arguments = method.idl_type.union_arguments
    if this_union_arguments:
        cpp_arguments.extend(this_union_arguments)

    if 'RaisesException' in method.extended_attributes:
        cpp_arguments.append('es')

    cpp_method_name = DartUtilities.scoped_name(interface, method, DartUtilities.cpp_name(method))
    return '%s(%s)' % (cpp_method_name, ', '.join(cpp_arguments))


# Mapping of IDL type to DartUtilities helper types.
def dart_arg_type(argument_type):
    if (argument_type.cpp_type == 'String'):
        return 'DartStringAdapter'

    return argument_type.cpp_type


def dart_set_return_value(interface_name, method, cpp_value, for_main_world=False):
    idl_type = method.idl_type
    extended_attributes = method.extended_attributes
    if idl_type.name == 'void':
        return None

    release = False

    if idl_type.is_union_type:
        release = idl_type.release

    # [CallWith=ScriptState], [RaisesException]
# TODO(terry): Disable ScriptState temporarily need to handle.
#    if (has_extended_attribute_value(method, 'CallWith', 'ScriptState') or
#        'RaisesException' in extended_attributes or
#        idl_type.is_union_type):
#        cpp_value = 'result'  # use local variable for value
#        release = idl_type.release

    auto_scope = not 'DartNoAutoScope' in extended_attributes
    script_wrappable = 'impl' if inherits_interface(interface_name, 'Node') else ''
    return idl_type.dart_set_return_value(cpp_value, extended_attributes,
                                          script_wrappable=script_wrappable,
                                          release=release,
                                          for_main_world=for_main_world,
                                          auto_scope=auto_scope)


def dart_value_to_local_cpp_value(interface, argument, index, auto_scope=True):
    extended_attributes = argument.extended_attributes
    interface_extended_attributes = interface.extended_attributes
    idl_type = argument.idl_type
    name = argument.name
    # TODO(terry): Variadic arguments are not handled but treated as one argument.
    #    if argument.is_variadic:
    #        vector_type = 'WillBeHeapVector' if idl_type.is_will_be_garbage_collected else 'Vector'
    #        return 'V8TRYCATCH_VOID({vector_type}<{cpp_type}>, {name}, toNativeArguments<{cpp_type}>(info, {index}))'.format(
    #                cpp_type=idl_type.cpp_type, name=name, index=index, vector_type=vector_type)

    # FIXME: V8 has some special logic around the addEventListener and
    # removeEventListener methods that should be added in somewhere.
    # There is also some logic in systemnative.py to force a null check
    # for the useCapture argument of those same methods that we may need to
    # pull over.
    null_check = (argument.is_optional and \
                  (idl_type.is_callback_interface or idl_type == 'Dictionary')) or \
                 (argument.default_value and argument.default_value.is_null)

    return idl_type.dart_value_to_local_cpp_value(
        interface_extended_attributes, extended_attributes, name, null_check,
        index=index, auto_scope=auto_scope)


################################################################################
# Auxiliary functions
################################################################################

# [NotEnumerable]
def property_attributes(method):
    extended_attributes = method.extended_attributes
    property_attributes_list = []
    if 'NotEnumerable' in extended_attributes:
        property_attributes_list.append('v8::DontEnum')
    if 'ReadOnly' in extended_attributes:
        property_attributes_list.append('v8::ReadOnly')
    if property_attributes_list:
        property_attributes_list.insert(0, 'v8::DontDelete')
    return property_attributes_list


def union_arguments(idl_type):
    """Return list of ['result0Enabled', 'result0', 'result1Enabled', ...] for union types, for use in setting return value"""
    return [arg
            for i in range(len(idl_type.member_types))
            for arg in ['result%sEnabled' % i, 'result%s' % i]]

IdlType.union_arguments = property(lambda self: None)
IdlUnionType.union_arguments = property(union_arguments)
