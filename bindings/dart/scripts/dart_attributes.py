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

"""Generate template values for attributes.

Extends IdlType with property |constructor_type_name|.

Design doc: http://www.chromium.org/developers/design-documents/idl-compiler
"""

import idl_types
from idl_types import inherits_interface
from dart_interface import suppress_getter, suppress_setter
import dart_types
from dart_utilities import DartUtilities
from v8_globals import includes, interfaces


def generate_attribute(interface, attribute):
    idl_type = attribute.idl_type
    base_idl_type = idl_type.base_type
    extended_attributes = attribute.extended_attributes

    idl_type.add_includes_for_type()

    # [CheckSecurity]
    is_check_security_for_node = 'CheckSecurity' in extended_attributes
    if is_check_security_for_node:
        includes.add('bindings/common/BindingSecurity.h')
    # [Custom]
    has_custom_getter = (('Custom' in extended_attributes and
                          extended_attributes['Custom'] in [None, 'Getter']) or
                         ('DartCustom' in extended_attributes and
                          extended_attributes['DartCustom'] in [None, 'Getter', 'New']))
    has_custom_setter = (not attribute.is_read_only and
                         (('Custom' in extended_attributes and
                          extended_attributes['Custom'] in [None, 'Setter']) or
                         ('DartCustom' in extended_attributes and
                          extended_attributes['DartCustom'] in [None, 'Setter', 'New'])))

    is_call_with_script_state = DartUtilities.has_extended_attribute_value(attribute, 'CallWith', 'ScriptState')

    # [CustomElementCallbacks], [Reflect]
    is_custom_element_callbacks = 'CustomElementCallbacks' in extended_attributes
    is_reflect = 'Reflect' in extended_attributes
    if is_custom_element_callbacks or is_reflect:
        includes.add('core/dom/custom/CustomElementCallbackDispatcher.h')
    # [RaisesException], [RaisesException=Setter]
    is_setter_raises_exception = (
        'RaisesException' in extended_attributes and
        extended_attributes['RaisesException'] in [None, 'Setter'])
    # [DartStrictTypeChecking]
    has_strict_type_checking = (
        ('DartStrictTypeChecking' in extended_attributes or
         'DartStrictTypeChecking' in interface.extended_attributes) and
        idl_type.is_wrapper_type)

    if (base_idl_type == 'EventHandler' and
        interface.name in ['Window', 'WorkerGlobalScope'] and
        attribute.name == 'onerror'):
        includes.add('bindings/v8/V8ErrorHandler.h')

    is_auto_scope = not 'DartNoAutoScope' in extended_attributes
    contents = {
        'access_control_list': access_control_list(attribute),
        'activity_logging_world_list_for_getter': DartUtilities.activity_logging_world_list(attribute, 'Getter'),  # [ActivityLogging]
        'activity_logging_world_list_for_setter': DartUtilities.activity_logging_world_list(attribute, 'Setter'),  # [ActivityLogging]
        'cached_attribute_validation_method': extended_attributes.get('CachedAttribute'),
        'conditional_string': DartUtilities.conditional_string(attribute),
        'constructor_type': idl_type.constructor_type_name
                            if is_constructor_attribute(attribute) else None,
        'cpp_name': DartUtilities.cpp_name(attribute),
        'cpp_type': idl_type.cpp_type,
        'deprecate_as': DartUtilities.deprecate_as(attribute),  # [DeprecateAs]
        'enum_validation_expression': idl_type.enum_validation_expression,
        'has_custom_getter': has_custom_getter,
        'has_custom_setter': has_custom_setter,
        'has_strict_type_checking': has_strict_type_checking,
        'idl_type': str(idl_type),  # need trailing [] on array for Dictionary::ConversionContext::setConversionType
        'is_auto_scope': is_auto_scope,
        'auto_scope': DartUtilities.bool_to_cpp(is_auto_scope),
        'is_call_with_execution_context': DartUtilities.has_extended_attribute_value(attribute, 'CallWith', 'ExecutionContext'),
        'is_call_with_script_state': is_call_with_script_state,
        'is_check_security_for_node': is_check_security_for_node,
        'is_custom_element_callbacks': is_custom_element_callbacks,
        'is_expose_js_accessors': 'ExposeJSAccessors' in extended_attributes,
        'is_getter_raises_exception': (  # [RaisesException]
            'RaisesException' in extended_attributes and
            extended_attributes['RaisesException'] in [None, 'Getter']),
        'is_partial_interface_member':  'PartialInterfaceImplementedAs' in extended_attributes,
        'is_initialized_by_event_constructor':
            'InitializedByEventConstructor' in extended_attributes,
        'is_keep_alive_for_gc': is_keep_alive_for_gc(interface, attribute),
        'is_nullable': attribute.idl_type.is_nullable,
        'is_per_world_bindings': 'PerWorldBindings' in extended_attributes,
        'is_read_only': attribute.is_read_only,
        'is_reflect': is_reflect,
        'is_replaceable': 'Replaceable' in attribute.extended_attributes,
        'is_setter_call_with_execution_context': DartUtilities.has_extended_attribute_value(attribute, 'SetterCallWith', 'ExecutionContext'),
        'is_setter_raises_exception': is_setter_raises_exception,
        'has_setter_exception_state': (
            is_setter_raises_exception or has_strict_type_checking or
            idl_type.is_integer_type),
        'is_static': attribute.is_static,
        'is_url': 'URL' in extended_attributes,
        'is_unforgeable': 'Unforgeable' in extended_attributes,
        'measure_as': DartUtilities.measure_as(attribute),  # [MeasureAs]
        'name': attribute.name,
        'per_context_enabled_function': DartUtilities.per_context_enabled_function_name(attribute),  # [PerContextEnabled]
        'property_attributes': property_attributes(attribute),
        'put_forwards': 'PutForwards' in extended_attributes,
        'ref_ptr': 'RefPtrWillBeRawPtr' if idl_type.is_will_be_garbage_collected else 'RefPtr',
        'reflect_empty': extended_attributes.get('ReflectEmpty'),
        'reflect_invalid': extended_attributes.get('ReflectInvalid', ''),
        'reflect_missing': extended_attributes.get('ReflectMissing'),
        'reflect_only': extended_attributes['ReflectOnly'].split('|')
            if 'ReflectOnly' in extended_attributes else None,
        'setter_callback': setter_callback_name(interface, attribute),
        'v8_type': dart_types.v8_type(base_idl_type),
        'runtime_enabled_function': DartUtilities.runtime_enabled_function_name(attribute),  # [RuntimeEnabled]
        'world_suffixes': ['', 'ForMainWorld']
                          if 'PerWorldBindings' in extended_attributes
                          else [''],  # [PerWorldBindings]
    }

    if is_constructor_attribute(attribute):
        generate_constructor_getter(interface, attribute, contents)
        return contents
    if not has_custom_getter:
        generate_getter(interface, attribute, contents)
    # FIXME: We did not previously support the PutForwards attribute, so I am
    # disabling it here for now to get things compiling.
    # We may wish to revisit this.
    # if ((not attribute.is_read_only or 'PutForwards' in extended_attributes)):
    if (not attribute.is_read_only):
        generate_setter(interface, attribute, contents)

    native_entry_getter = \
        DartUtilities.generate_native_entry(interface.name, contents,
                                            attribute.name, 'Getter',
                                            None, [], None)
    native_entry_setter = \
        DartUtilities.generate_native_entry(interface.name, contents,
                                            attribute.name, 'Setter',
                                            None, ["value"], None)
    contents.update({
        'native_entry_getter': native_entry_getter,
        'native_entry_setter': native_entry_setter,
    })

    return contents


################################################################################
# Getter
################################################################################

def generate_getter(interface, attribute, contents):
    idl_type = attribute.idl_type
    base_idl_type = idl_type.base_type
    extended_attributes = attribute.extended_attributes
    name = attribute.name

    cpp_value = getter_expression(interface, attribute, contents)
    # Normally we can inline the function call into the return statement to
    # avoid the overhead of using a Ref<> temporary, but for some cases
    # (nullable types, EventHandler, [CachedAttribute], or if there are
    # exceptions), we need to use a local variable.
    # FIXME: check if compilers are smart enough to inline this, and if so,
    # always use a local variable (for readability and CG simplicity).
    release = False
    if (idl_type.is_nullable or
        base_idl_type == 'EventHandler' or
        'CachedAttribute' in extended_attributes or
        'ReflectOnly' in extended_attributes or
        contents['is_getter_raises_exception']):
        contents['cpp_value_original'] = cpp_value
        cpp_value = 'result'
        # EventHandler has special handling
        if base_idl_type != 'EventHandler' and idl_type.is_interface_type:
            release = True

    dart_set_return_value = \
        idl_type.dart_set_return_value(cpp_value,
                                       extended_attributes=extended_attributes,
                                       script_wrappable='impl',
                                       release=release,
                                       for_main_world=False,
                                       auto_scope=contents['is_auto_scope'])

    # TODO(terry): Should be able to eliminate suppress_getter as we move from
    #              IGNORE_MEMBERS to DartSuppress in the IDL.
    suppress = (suppress_getter(interface.name, attribute.name) or
                DartUtilities.has_extended_attribute_value(attribute, 'DartSuppress', 'Getter'))

    contents.update({
        'cpp_value': cpp_value,
        'dart_set_return_value': dart_set_return_value,
        'is_getter_suppressed': suppress,
    })


def getter_expression(interface, attribute, contents):
    arguments = []
    idl_type = attribute.idl_type
    this_getter_base_name = getter_base_name(interface, attribute, arguments)
    getter_name = DartUtilities.scoped_name(interface, attribute, this_getter_base_name)

    arguments.extend(DartUtilities.call_with_arguments(attribute))
    if ('PartialInterfaceImplementedAs' in attribute.extended_attributes and
        not attribute.is_static):
        # Pass by reference.
        arguments.append('*receiver')

    # TODO(jacobr): refactor has_type_checking_nullable to better match v8.
    has_type_checking_nullable = (
        (DartUtilities.has_extended_attribute_value(interface, 'TypeChecking', 'Nullable') or
         DartUtilities.has_extended_attribute_value(attribute, 'TypeChecking', 'Nullable')) and
         idl_type.is_wrapper_type)

    if attribute.idl_type.is_nullable and not has_type_checking_nullable:
        arguments.append('isNull')
    if contents['is_getter_raises_exception']:
        arguments.append('es')
    return '%s(%s)' % (getter_name, ', '.join(arguments))


CONTENT_ATTRIBUTE_GETTER_NAMES = {
    'boolean': 'hasAttribute',
    'long': 'getIntegralAttribute',
    'unsigned long': 'getUnsignedIntegralAttribute',
}


def getter_base_name(interface, attribute, arguments):
    extended_attributes = attribute.extended_attributes
    if 'Reflect' not in extended_attributes:
        return DartUtilities.uncapitalize(DartUtilities.cpp_name(attribute))

    content_attribute_name = extended_attributes['Reflect'] or attribute.name.lower()
    if content_attribute_name in ['class', 'id', 'name']:
        # Special-case for performance optimization.
        return 'get%sAttribute' % content_attribute_name.capitalize()

    arguments.append(scoped_content_attribute_name(interface, attribute))

    base_idl_type = attribute.idl_type.base_type
    if base_idl_type in CONTENT_ATTRIBUTE_GETTER_NAMES:
        return CONTENT_ATTRIBUTE_GETTER_NAMES[base_idl_type]
    if 'URL' in attribute.extended_attributes:
        return 'getURLAttribute'
    return 'getAttribute'


def is_keep_alive_for_gc(interface, attribute):
    idl_type = attribute.idl_type
    base_idl_type = idl_type.base_type
    extended_attributes = attribute.extended_attributes
    return (
        # For readonly attributes, for performance reasons we keep the attribute
        # wrapper alive while the owner wrapper is alive, because the attribute
        # never changes.
        (attribute.is_read_only and
         idl_type.is_wrapper_type and
         # There are some exceptions, however:
         not(
             # Node lifetime is managed by object grouping.
             inherits_interface(interface.name, 'Node') or
             inherits_interface(base_idl_type, 'Node') or
             # A self-reference is unnecessary.
             attribute.name == 'self' or
             # FIXME: Remove these hard-coded hacks.
             base_idl_type in ['EventTarget', 'Window'] or
             base_idl_type.startswith(('HTML', 'SVG')))))


################################################################################
# Setter
################################################################################

def generate_setter(interface, attribute, contents):
    def target_attribute():
        target_interface_name = attribute.idl_type.base_type
        target_attribute_name = extended_attributes['PutForwards']
        target_interface = interfaces[target_interface_name]
        try:
            return next(attribute
                        for attribute in target_interface.attributes
                        if attribute.name == target_attribute_name)
        except StopIteration:
            raise Exception('[PutForward] target not found:\n'
                            'Attribute "%s" is not present in interface "%s"' %
                            (target_attribute_name, target_interface_name))

    extended_attributes = attribute.extended_attributes
    interface_extended_attributes = interface.extended_attributes

    if 'PutForwards' in extended_attributes:
        # Use target attribute in place of original attribute
        attribute = target_attribute()
        this_cpp_type = 'DartStringAdapter'
    else:
        this_cpp_type = contents['cpp_type']

    idl_type = attribute.idl_type

    # TODO(terry): Should be able to eliminate suppress_setter as we move from
    #              IGNORE_MEMBERS to DartSuppress in the IDL.
    suppress = (suppress_setter(interface.name, attribute.name) or
                DartUtilities.has_extended_attribute_value(attribute, 'DartSuppress', 'Setter'))
    contents.update({
        'is_setter_suppressed':  suppress,
        'setter_lvalue': dart_types.check_reserved_name(attribute.name),
        'cpp_type': this_cpp_type,
        'local_cpp_type': idl_type.cpp_type_args(attribute.extended_attributes, used_as_argument=True),
        'cpp_setter': setter_expression(interface, attribute, contents),
        'dart_value_to_local_cpp_value':
            attribute.idl_type.dart_value_to_local_cpp_value(
                interface_extended_attributes, extended_attributes, attribute.name, False, 1,
                contents['is_auto_scope']),
    })


def setter_expression(interface, attribute, contents):
    extended_attributes = attribute.extended_attributes
    arguments = DartUtilities.call_with_arguments(attribute, extended_attributes.get('SetterCallWith'))

    this_setter_base_name = setter_base_name(interface, attribute, arguments)
    setter_name = DartUtilities.scoped_name(interface, attribute, this_setter_base_name)

    if ('PartialInterfaceImplementedAs' in extended_attributes and
        not attribute.is_static):
        arguments.append('*receiver')
    idl_type = attribute.idl_type
    if idl_type.base_type == 'EventHandler':
        getter_name = DartUtilities.scoped_name(interface, attribute, DartUtilities.cpp_name(attribute))
        contents['event_handler_getter_expression'] = '%s(%s)' % (
            getter_name, ', '.join(arguments))
        # FIXME(vsm): Do we need to support this? If so, what's our analogue of
        # V8EventListenerList?
        arguments.append('nullptr')
        # if (interface.name in ['Window', 'WorkerGlobalScope'] and
        #    attribute.name == 'onerror'):
        #    includes.add('bindings/v8/V8ErrorHandler.h')
        #    arguments.append('V8EventListenerList::findOrCreateWrapper<V8ErrorHandler>(jsValue, true, info.GetIsolate())')
        # else:
        #    arguments.append('V8EventListenerList::getEventListener(jsValue, true, ListenerFindOrCreate)')
    else:
        attribute_name = dart_types.check_reserved_name(attribute.name)
        arguments.append(attribute_name)
    if contents['is_setter_raises_exception']:
        arguments.append('es')

    return '%s(%s)' % (setter_name, ', '.join(arguments))


CONTENT_ATTRIBUTE_SETTER_NAMES = {
    'boolean': 'setBooleanAttribute',
    'long': 'setIntegralAttribute',
    'unsigned long': 'setUnsignedIntegralAttribute',
}


def setter_base_name(interface, attribute, arguments):
    if 'Reflect' not in attribute.extended_attributes:
        return 'set%s' % DartUtilities.capitalize(DartUtilities.cpp_name(attribute))
    arguments.append(scoped_content_attribute_name(interface, attribute))

    base_idl_type = attribute.idl_type.base_type
    if base_idl_type in CONTENT_ATTRIBUTE_SETTER_NAMES:
        return CONTENT_ATTRIBUTE_SETTER_NAMES[base_idl_type]
    return 'setAttribute'


def scoped_content_attribute_name(interface, attribute):
    content_attribute_name = attribute.extended_attributes['Reflect'] or attribute.name.lower()
    namespace = 'SVGNames' if interface.name.startswith('SVG') else 'HTMLNames'
    includes.add('%s.h' % namespace)
    return 'WebCore::%s::%sAttr' % (namespace, content_attribute_name)


################################################################################
# Attribute configuration
################################################################################

# [Replaceable]
def setter_callback_name(interface, attribute):
    cpp_class_name = DartUtilities.cpp_name(interface)
    extended_attributes = attribute.extended_attributes
    if (('Replaceable' in extended_attributes and
         'PutForwards' not in extended_attributes) or
        is_constructor_attribute(attribute)):
        # FIXME: rename to ForceSetAttributeOnThisCallback, since also used for Constructors
        return '{0}V8Internal::{0}ReplaceableAttributeSetterCallback'.format(cpp_class_name)
    # FIXME:disabling PutForwards for now since we didn't support it before
    #    if attribute.is_read_only and 'PutForwards' not in extended_attributes:
    if attribute.is_read_only:
        return '0'
    return '%sV8Internal::%sAttributeSetterCallback' % (cpp_class_name, attribute.name)


# [DoNotCheckSecurity], [Unforgeable]
def access_control_list(attribute):
    extended_attributes = attribute.extended_attributes
    access_control = []
    if 'DoNotCheckSecurity' in extended_attributes:
        do_not_check_security = extended_attributes['DoNotCheckSecurity']
        if do_not_check_security == 'Setter':
            access_control.append('v8::ALL_CAN_WRITE')
        else:
            access_control.append('v8::ALL_CAN_READ')
            if (not attribute.is_read_only or
                'Replaceable' in extended_attributes):
                access_control.append('v8::ALL_CAN_WRITE')
    if 'Unforgeable' in extended_attributes:
        access_control.append('v8::PROHIBITS_OVERWRITING')
    return access_control or ['v8::DEFAULT']


# [NotEnumerable], [Unforgeable]
def property_attributes(attribute):
    extended_attributes = attribute.extended_attributes
    property_attributes_list = []
    if ('NotEnumerable' in extended_attributes or
        is_constructor_attribute(attribute)):
        property_attributes_list.append('v8::DontEnum')
    if 'Unforgeable' in extended_attributes:
        property_attributes_list.append('v8::DontDelete')
    return property_attributes_list or ['v8::None']


################################################################################
# Constructors
################################################################################

idl_types.IdlType.constructor_type_name = property(
    # FIXME: replace this with a [ConstructorAttribute] extended attribute
    lambda self: DartUtilities.strip_suffix(self.base_type, 'Constructor'))


def is_constructor_attribute(attribute):
    # FIXME: replace this with [ConstructorAttribute] extended attribute
    return attribute.idl_type.base_type.endswith('Constructor')


def generate_constructor_getter(interface, attribute, contents):
    contents['needs_constructor_getter_callback'] = contents['measure_as'] or contents['deprecate_as']
