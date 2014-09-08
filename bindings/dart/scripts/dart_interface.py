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

"""Generate template values for an interface.

Design doc: http://www.chromium.org/developers/design-documents/idl-compiler
"""

from collections import defaultdict

import idl_types
from idl_types import IdlType, inherits_interface
import dart_attributes
import dart_methods
import dart_types
from dart_utilities import DartUtilities
from v8_globals import includes


INTERFACE_H_INCLUDES = frozenset([
    'bindings/dart/DartDOMWrapper.h',
    'platform/heap/Handle.h',
])

INTERFACE_CPP_INCLUDES = frozenset([
    'DartUtilities.h',
    'wtf/GetPtr.h',
    'wtf/RefPtr.h',
])


# TODO(terry): Temporary to not generate a method, getter/setter. Format is:
#
#               interface_name.method_name
#               interface_name.get:attribute_name
#               interface_name.set:attribute_name
#
#               Ultimate solution add a special attribute flag to IDL to signal
#               don't generate IDL entry in Dart (e.g., DartNoGenerate)?
IGNORE_MEMBERS = frozenset([
    'AudioBufferSourceNode.looping',  # TODO(vsm): Use deprecated IDL annotation
    'CSSStyleDeclaration.getPropertyCSSValue',
    'CanvasRenderingContext2D.clearShadow',
    'CanvasRenderingContext2D.drawImageFromRect',
    'CanvasRenderingContext2D.setAlpha',
    'CanvasRenderingContext2D.setCompositeOperation',
    'CanvasRenderingContext2D.setFillColor',
    'CanvasRenderingContext2D.setLineCap',
    'CanvasRenderingContext2D.setLineJoin',
    'CanvasRenderingContext2D.setLineWidth',
    'CanvasRenderingContext2D.setMiterLimit',
    'CanvasRenderingContext2D.setShadow',
    'CanvasRenderingContext2D.setStrokeColor',
    'CharacterData.remove',
    'Window.call:blur',
    'Window.call:focus',
    'Window.clientInformation',
    'Window.createImageBitmap',
    'Window.get:frames',
    'Window.get:length',
    'Window.on:beforeUnload',
    'Window.on:webkitTransitionEnd',
    'Window.pagePopupController',
    'Window.prompt',
    'Window.webkitCancelAnimationFrame',
    'Window.webkitCancelRequestAnimationFrame',
    'Window.webkitIndexedDB',
    'Window.webkitRequestAnimationFrame',
    'Document.alinkColor',
    'HTMLDocument.all',
    'Document.applets',
    'Document.bgColor',
    'Document.clear',
    'Document.createAttribute',
    'Document.createAttributeNS',
    'Document.createComment',
    'Document.createExpression',
    'Document.createNSResolver',
    'Document.createProcessingInstruction',
    'Document.designMode',
    'Document.dir',
    'Document.evaluate',
    'Document.fgColor',
    'Document.get:URL',
    'Document.get:anchors',
    'Document.get:characterSet',
    'Document.get:compatMode',
    'Document.get:defaultCharset',
    'Document.get:doctype',
    'Document.get:documentURI',
    'Document.get:embeds',
    'Document.get:forms',
    'Document.get:inputEncoding',
    'Document.get:links',
    'Document.get:plugins',
    'Document.get:scripts',
    'Document.get:xmlEncoding',
    'Document.getElementsByTagNameNS',
    'Document.getOverrideStyle',
    'Document.getSelection',
    'Document.images',
    'Document.linkColor',
    'Document.location',
    'Document.on:wheel',
    'Document.open',
    'Document.register',
    'Document.set:domain',
    'Document.vlinkColor',
    'Document.webkitCurrentFullScreenElement',
    'Document.webkitFullScreenKeyboardInputAllowed',
    'Document.write',
    'Document.writeln',
    'Document.xmlStandalone',
    'Document.xmlVersion',
    'DocumentFragment.children',
    'DocumentType.*',
    'DOMException.code',
    'DOMException.ABORT_ERR',
    'DOMException.DATA_CLONE_ERR',
    'DOMException.DOMSTRING_SIZE_ERR',
    'DOMException.HIERARCHY_REQUEST_ERR',
    'DOMException.INDEX_SIZE_ERR',
    'DOMException.INUSE_ATTRIBUTE_ERR',
    'DOMException.INVALID_ACCESS_ERR',
    'DOMException.INVALID_CHARACTER_ERR',
    'DOMException.INVALID_MODIFICATION_ERR',
    'DOMException.INVALID_NODE_TYPE_ERR',
    'DOMException.INVALID_STATE_ERR',
    'DOMException.NAMESPACE_ERR',
    'DOMException.NETWORK_ERR',
    'DOMException.NOT_FOUND_ERR',
    'DOMException.NOT_SUPPORTED_ERR',
    'DOMException.NO_DATA_ALLOWED_ERR',
    'DOMException.NO_MODIFICATION_ALLOWED_ERR',
    'DOMException.QUOTA_EXCEEDED_ERR',
    'DOMException.SECURITY_ERR',
    'DOMException.SYNTAX_ERR',
    'DOMException.TIMEOUT_ERR',
    'DOMException.TYPE_MISMATCH_ERR',
    'DOMException.URL_MISMATCH_ERR',
    'DOMException.VALIDATION_ERR',
    'DOMException.WRONG_DOCUMENT_ERR',
    'Element.accessKey',
    'Element.dataset',
    'Element.get:classList',
    'Element.getAttributeNode',
    'Element.getAttributeNodeNS',
    'Element.getElementsByTagNameNS',
    'Element.innerText',
    'Element.on:wheel',
    'Element.outerText',
    'Element.removeAttributeNode',
    'Element.set:outerHTML',
    'Element.setAttributeNode',
    'Element.setAttributeNodeNS',
    'Element.webkitCreateShadowRoot',
    'Element.webkitMatchesSelector',
    'Element.webkitPseudo',
    'Element.webkitShadowRoot',
    '=Event.returnValue',  # Only suppress on Event, allow for BeforeUnloadEvent.
    'Event.srcElement',
    'EventSource.URL',
    'FontFace.ready',
    'FontFaceSet.load',
    'FontFaceSet.ready',
    'HTMLAnchorElement.charset',
    'HTMLAnchorElement.coords',
    'HTMLAnchorElement.rev',
    'HTMLAnchorElement.shape',
    'HTMLAnchorElement.text',
    'HTMLAppletElement.*',
    'HTMLAreaElement.noHref',
    'HTMLBRElement.clear',
    'HTMLBaseFontElement.*',
    'HTMLBodyElement.aLink',
    'HTMLBodyElement.background',
    'HTMLBodyElement.bgColor',
    'HTMLBodyElement.link',
    'HTMLBodyElement.on:beforeUnload',
    'HTMLBodyElement.text',
    'HTMLBodyElement.vLink',
    'HTMLDListElement.compact',
    'HTMLDirectoryElement.*',
    'HTMLDivElement.align',
    'HTMLFontElement.*',
    'HTMLFormControlsCollection.__getter__',
    'HTMLFormElement.get:elements',
    'HTMLFrameElement.*',
    'HTMLFrameSetElement.*',
    'HTMLHRElement.align',
    'HTMLHRElement.noShade',
    'HTMLHRElement.size',
    'HTMLHRElement.width',
    'HTMLHeadElement.profile',
    'HTMLHeadingElement.align',
    'HTMLHtmlElement.manifest',
    'HTMLHtmlElement.version',
    'HTMLIFrameElement.align',
    'HTMLIFrameElement.frameBorder',
    'HTMLIFrameElement.longDesc',
    'HTMLIFrameElement.marginHeight',
    'HTMLIFrameElement.marginWidth',
    'HTMLIFrameElement.scrolling',
    'HTMLImageElement.align',
    'HTMLImageElement.hspace',
    'HTMLImageElement.longDesc',
    'HTMLImageElement.name',
    'HTMLImageElement.vspace',
    'HTMLInputElement.align',
    'HTMLLegendElement.align',
    'HTMLLinkElement.charset',
    'HTMLLinkElement.rev',
    'HTMLLinkElement.target',
    'HTMLMarqueeElement.*',
    'HTMLMenuElement.compact',
    'HTMLMetaElement.scheme',
    'HTMLOListElement.compact',
    'HTMLObjectElement.align',
    'HTMLObjectElement.archive',
    'HTMLObjectElement.border',
    'HTMLObjectElement.codeBase',
    'HTMLObjectElement.codeType',
    'HTMLObjectElement.declare',
    'HTMLObjectElement.hspace',
    'HTMLObjectElement.standby',
    'HTMLObjectElement.vspace',
    'HTMLOptionElement.text',
    'HTMLOptionsCollection.*',
    'HTMLParagraphElement.align',
    'HTMLParamElement.type',
    'HTMLParamElement.valueType',
    'HTMLPreElement.width',
    'HTMLScriptElement.text',
    'HTMLSelectElement.options',
    'HTMLSelectElement.selectedOptions',
    'HTMLTableCaptionElement.align',
    'HTMLTableCellElement.abbr',
    'HTMLTableCellElement.align',
    'HTMLTableCellElement.axis',
    'HTMLTableCellElement.bgColor',
    'HTMLTableCellElement.ch',
    'HTMLTableCellElement.chOff',
    'HTMLTableCellElement.height',
    'HTMLTableCellElement.noWrap',
    'HTMLTableCellElement.scope',
    'HTMLTableCellElement.vAlign',
    'HTMLTableCellElement.width',
    'HTMLTableColElement.align',
    'HTMLTableColElement.ch',
    'HTMLTableColElement.chOff',
    'HTMLTableColElement.vAlign',
    'HTMLTableColElement.width',
    'HTMLTableElement.align',
    'HTMLTableElement.bgColor',
    'HTMLTableElement.cellPadding',
    'HTMLTableElement.cellSpacing',
    'HTMLTableElement.frame',
    'HTMLTableElement.rules',
    'HTMLTableElement.summary',
    'HTMLTableElement.width',
    'HTMLTableRowElement.align',
    'HTMLTableRowElement.bgColor',
    'HTMLTableRowElement.ch',
    'HTMLTableRowElement.chOff',
    'HTMLTableRowElement.vAlign',
    'HTMLTableSectionElement.align',
    'HTMLTableSectionElement.ch',
    'HTMLTableSectionElement.chOff',
    'HTMLTableSectionElement.vAlign',
    'HTMLTitleElement.text',
    'HTMLUListElement.compact',
    'HTMLUListElement.type',
    'Location.valueOf',
    'MessageEvent.ports',
    'MessageEvent.webkitInitMessageEvent',
    'MouseEvent.x',
    'MouseEvent.y',
    'Navigator.registerServiceWorker',
    'Navigator.unregisterServiceWorker',
    'Node.compareDocumentPosition',
    'Node.get:DOCUMENT_POSITION_CONTAINED_BY',
    'Node.get:DOCUMENT_POSITION_CONTAINS',
    'Node.get:DOCUMENT_POSITION_DISCONNECTED',
    'Node.get:DOCUMENT_POSITION_FOLLOWING',
    'Node.get:DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC',
    'Node.get:DOCUMENT_POSITION_PRECEDING',
    'Node.get:prefix',
    'Node.hasAttributes',
    'Node.isDefaultNamespace',
    'Node.isEqualNode',
    'Node.isSameNode',
    'Node.isSupported',
    'Node.lookupNamespaceURI',
    'Node.lookupPrefix',
    'Node.normalize',
    'Node.set:nodeValue',
    'NodeFilter.acceptNode',
    'NodeIterator.expandEntityReferences',
    'NodeIterator.filter',
    'Performance.webkitClearMarks',
    'Performance.webkitClearMeasures',
    'Performance.webkitGetEntries',
    'Performance.webkitGetEntriesByName',
    'Performance.webkitGetEntriesByType',
    'Performance.webkitMark',
    'Performance.webkitMeasure',
    'ShadowRoot.getElementsByTagNameNS',
    'SVGElement.getPresentationAttribute',
    'SVGElementInstance.on:wheel',
    'WheelEvent.wheelDelta',
    'Window.on:wheel',
    'WindowEventHandlers.on:beforeUnload',
    'WorkerGlobalScope.webkitIndexedDB',
# TODO(jacobr): should these be removed?
    'Document.close',
    'Document.hasFocus',
])


def _suppress_method(interface_name, name):
    name_to_find = '%s.%s' % (interface_name, name)
    wildcard_name_to_find = '%s.*' % interface_name
    return name_to_find in IGNORE_MEMBERS or wildcard_name_to_find in IGNORE_MEMBERS


# Both getter and setter are to be suppressed then the attribute is completely
# disappear.
def _suppress_attribute(interface_name, name):
    return (suppress_getter(interface_name, name) and suppress_setter(interface_name, name))


def suppress_getter(interface_name, name):
    name_to_find = '%s.get:%s' % (interface_name, name)
    wildcard_getter_to_find = '%s.get:*' % interface_name
    return (name_to_find in IGNORE_MEMBERS or
            _suppress_method(interface_name, name) or
            wildcard_getter_to_find in IGNORE_MEMBERS)


def suppress_setter(interface_name, name):
    name_to_find = '%s.set:%s' % (interface_name, name)
    wildcard_setter_to_find = '%s.set:*' % interface_name
    return (name_to_find in IGNORE_MEMBERS or
            _suppress_method(interface_name, name) or
            wildcard_setter_to_find in IGNORE_MEMBERS)


# To suppress an IDL method or attribute with a particular Extended Attribute
# w/o a value e.g, StrictTypeChecking would be an empty set
#   'StrictTypeChecking': frozenset([]),
IGNORE_EXTENDED_ATTRIBUTES = {
#    'RuntimeEnabled': frozenset(['ExperimentalCanvasFeatures']),
}


# Return True if the method / attribute should be suppressed.
def _suppress_extended_attributes(extended_attributes):
    if 'DartSuppress' in extended_attributes and extended_attributes.get('DartSuppress') == None:
        return True

    # TODO(terry): Eliminate this using DartSuppress extended attribute in the
    #              IDL files instead of the IGNORE_EXTENDED_ATTRIBUTES list.
    for extended_attribute_name in extended_attributes:
        ignore_extended_values = IGNORE_EXTENDED_ATTRIBUTES.get(extended_attribute_name)
        if ignore_extended_values != None:
            extended_attribute_value = extended_attributes.get(extended_attribute_name)
            if ((not ignore_extended_values and extended_attribute_value == None) or
                extended_attribute_value in ignore_extended_values):
                return True
    return False


def add_native_entries(interface, constructors, is_custom):
    for constructor in constructors:
        types = None
        if not is_custom:
            types = [arg['preprocessed_type']
                     for arg in constructor['arguments']]
        argument_names = [arg['name'] for arg in constructor['arguments']]
        native_entry = \
            DartUtilities.generate_native_entry(interface.name, constructor,
                                                None, 'Constructor', None,
                                                argument_names, types)
        constructor.update({'native_entry': native_entry})


def generate_interface(interface):
    includes.clear()
    includes.update(INTERFACE_CPP_INCLUDES)
    header_includes = set(INTERFACE_H_INCLUDES)

    parent_interface = interface.parent
    if parent_interface:
        header_includes.update(dart_types.includes_for_interface(parent_interface))
    extended_attributes = interface.extended_attributes

    is_audio_buffer = inherits_interface(interface.name, 'AudioBuffer')
    if is_audio_buffer:
        includes.add('modules/webaudio/AudioBuffer.h')

    is_document = inherits_interface(interface.name, 'Document')
    if is_document:
        # FIXME(vsm): We probably need bindings/dart/DartController and
        # core/frame/LocalFrame.h here.
        includes.update(['DartDocument.h'])

    if inherits_interface(interface.name, 'DataTransferItemList'):
        # FIXME(jacobr): this is a hack.
        includes.update(['core/html/HTMLCollection.h'])


    if inherits_interface(interface.name, 'EventTarget'):
        includes.update(['DartEventListener.h'])

    # [ActiveDOMObject]
    is_active_dom_object = 'ActiveDOMObject' in extended_attributes

    # [CheckSecurity]
    is_check_security = 'CheckSecurity' in extended_attributes
    if is_check_security:
        includes.add('bindings/common/BindingSecurity.h')

    # [DependentLifetime]
    is_dependent_lifetime = 'DependentLifetime' in extended_attributes

    # [MeasureAs]
# TODO(terry): Remove Me?
#    is_measure_as = 'MeasureAs' in extended_attributes
#    if is_measure_as:
#        includes.add('core/frame/UseCounter.h')

    # [SetWrapperReferenceFrom]
    reachable_node_function = extended_attributes.get('SetWrapperReferenceFrom')
    if reachable_node_function:
        # FIXME(vsm): We may need bindings/dart/DartGCController.h instead.
        includes.update(['bindings/v8/V8GCController.h',
                         'core/dom/Element.h'])

    # [SetWrapperReferenceTo]
    set_wrapper_reference_to_list = [{
        'name': argument.name,
        # FIXME: properly should be:
        # 'cpp_type': argument.idl_type.cpp_type_args(used_as_argument=True),
        # (if type is non-wrapper type like NodeFilter, normally RefPtr)
        # Raw pointers faster though, and NodeFilter hacky anyway.
        'cpp_type': argument.idl_type.implemented_as + '*',
        'idl_type': argument.idl_type,
        'v8_type': dart_types.v8_type(argument.idl_type.name),
    } for argument in extended_attributes.get('SetWrapperReferenceTo', [])]
    for set_wrapper_reference_to in set_wrapper_reference_to_list:
        set_wrapper_reference_to['idl_type'].add_includes_for_type()

    # [SpecialWrapFor]
    if 'SpecialWrapFor' in extended_attributes:
        special_wrap_for = extended_attributes['SpecialWrapFor'].split('|')
    else:
        special_wrap_for = []
    for special_wrap_interface in special_wrap_for:
        dart_types.add_includes_for_interface(special_wrap_interface)

    # [Custom=Wrap], [SetWrapperReferenceFrom]
    has_visit_dom_wrapper = (
        DartUtilities.has_extended_attribute_value(interface, 'Custom', 'VisitDOMWrapper') or
        reachable_node_function or
        set_wrapper_reference_to_list)

    this_gc_type = DartUtilities.gc_type(interface)

    template_contents = {
        'conditional_string': DartUtilities.conditional_string(interface),  # [Conditional]
        'cpp_class': DartUtilities.cpp_name(interface),
        'gc_type': this_gc_type,
        'has_custom_legacy_call_as_function': DartUtilities.has_extended_attribute_value(interface, 'Custom', 'LegacyCallAsFunction'),  # [Custom=LegacyCallAsFunction]
        'has_custom_to_v8': DartUtilities.has_extended_attribute_value(interface, 'Custom', 'ToV8'),  # [Custom=ToV8]
        'has_custom_wrap': DartUtilities.has_extended_attribute_value(interface, 'Custom', 'Wrap'),  # [Custom=Wrap]
        'has_visit_dom_wrapper': has_visit_dom_wrapper,
        'header_includes': header_includes,
        'interface_name': interface.name,
        'is_active_dom_object': is_active_dom_object,
        'is_audio_buffer': is_audio_buffer,
        'is_check_security': is_check_security,
        'is_dependent_lifetime': is_dependent_lifetime,
        'is_document': is_document,
        'is_event_target': inherits_interface(interface.name, 'EventTarget'),
        'is_exception': interface.is_exception,
        'is_garbage_collected': this_gc_type == 'GarbageCollectedObject',
        'is_will_be_garbage_collected': this_gc_type == 'WillBeGarbageCollectedObject',
        'is_node': inherits_interface(interface.name, 'Node'),
        'measure_as': DartUtilities.measure_as(interface),  # [MeasureAs]
        'parent_interface': parent_interface,
        'pass_cpp_type': dart_types.cpp_template_type(
            dart_types.cpp_ptr_type('PassRefPtr', 'RawPtr', this_gc_type),
            DartUtilities.cpp_name(interface)),
        'reachable_node_function': reachable_node_function,
        'runtime_enabled_function': DartUtilities.runtime_enabled_function_name(interface),  # [RuntimeEnabled]
        'set_wrapper_reference_to_list': set_wrapper_reference_to_list,
        'special_wrap_for': special_wrap_for,
        'dart_class': dart_types.dart_type(interface.name),
        'v8_class': DartUtilities.v8_class_name(interface),
        'wrapper_configuration': 'WrapperConfiguration::Dependent'
            if (has_visit_dom_wrapper or
                is_active_dom_object or
                is_dependent_lifetime)
            else 'WrapperConfiguration::Independent',
    }

    # Constructors
    constructors = [generate_constructor(interface, constructor)
                    for constructor in interface.constructors
                    # FIXME: shouldn't put named constructors with constructors
                    # (currently needed for Perl compatibility)
                    # Handle named constructors separately
                    if constructor.name == 'Constructor']
    generate_constructor_overloads(constructors)

    # [CustomConstructor]
    custom_constructors = [generate_custom_constructor(interface, constructor)
                           for constructor in interface.custom_constructors]

    # [EventConstructor]
    has_event_constructor = 'EventConstructor' in extended_attributes
    any_type_attributes = [attribute for attribute in interface.attributes
                           if attribute.idl_type.name == 'Any']
    if has_event_constructor:
        includes.add('bindings/common/Dictionary.h')
        if any_type_attributes:
            includes.add('bindings/v8/SerializedScriptValue.h')

    # [NamedConstructor]
    named_constructor = generate_named_constructor(interface)

    add_native_entries(interface, constructors, bool(custom_constructors))
    add_native_entries(interface, custom_constructors, bool(custom_constructors))
    if named_constructor:
        add_native_entries(interface, [named_constructor], bool(custom_constructors))

    if (constructors or custom_constructors or has_event_constructor or
        named_constructor):
        includes.add('core/frame/LocalDOMWindow.h')

    template_contents.update({
        'any_type_attributes': any_type_attributes,
        'constructors': constructors,
        'custom_constructors': custom_constructors,
        'has_custom_constructor': bool(custom_constructors),
        'has_event_constructor': has_event_constructor,
        'interface_length':
            interface_length(interface, constructors + custom_constructors),
        'is_constructor_call_with_document': DartUtilities.has_extended_attribute_value(
            interface, 'ConstructorCallWith', 'Document'),  # [ConstructorCallWith=Document]
        'is_constructor_call_with_execution_context': DartUtilities.has_extended_attribute_value(
            interface, 'ConstructorCallWith', 'ExecutionContext'),  # [ConstructorCallWith=ExeuctionContext]
        'is_constructor_raises_exception': extended_attributes.get('RaisesException') == 'Constructor',  # [RaisesException=Constructor]
        'named_constructor': named_constructor,
    })

    # Constants
    template_contents.update({
        'constants': [generate_constant(constant) for constant in interface.constants],
        'do_not_check_constants': 'DoNotCheckConstants' in extended_attributes,
    })

    # Attributes
    attributes = [dart_attributes.generate_attribute(interface, attribute)
                  for attribute in interface.attributes
                      # Skip attributes in the IGNORE_MEMBERS list or if an
                      # extended attribute is in the IGNORE_EXTENDED_ATTRIBUTES.
                      if (not _suppress_attribute(interface.name, attribute.name) and
                          not dart_attributes.is_constructor_attribute(attribute) and
                          not _suppress_extended_attributes(attribute.extended_attributes) and
                          not ('DartSuppress' in attribute.extended_attributes and
                           attribute.extended_attributes.get('DartSuppress') == None))]
    template_contents.update({
        'attributes': attributes,
        'has_accessors': any(attribute['is_expose_js_accessors'] for attribute in attributes),
        'has_attribute_configuration': any(
             not (attribute['is_expose_js_accessors'] or
                  attribute['is_static'] or
                  attribute['runtime_enabled_function'] or
                  attribute['per_context_enabled_function'])
             for attribute in attributes),
        'has_constructor_attributes': any(attribute['constructor_type'] for attribute in attributes),
        'has_per_context_enabled_attributes': any(attribute['per_context_enabled_function'] for attribute in attributes),
        'has_replaceable_attributes': any(attribute['is_replaceable'] for attribute in attributes),
    })

    # Methods
    methods = [dart_methods.generate_method(interface, method)
               for method in interface.operations
               # Skip anonymous special operations (methods name empty).
               # Skip methods in our IGNORE_MEMBERS list.
               # Skip methods w/ extended attributes in IGNORE_EXTENDED_ATTRIBUTES list.
               if (method.name and
                   # TODO(terry): Eventual eliminate the IGNORE_MEMBERS in favor of DartSupress.
                   not _suppress_method(interface.name, method.name) and
                   not _suppress_extended_attributes(method.extended_attributes) and
                   not 'DartSuppress' in method.extended_attributes)]
    generate_overloads(methods)
    for method in methods:
        method['do_generate_method_configuration'] = (
            method['do_not_check_signature'] and
            not method['per_context_enabled_function'] and
            # For overloaded methods, only generate one accessor
            ('overload_index' not in method or method['overload_index'] == 1))

    generate_method_native_entries(interface, methods)

    template_contents.update({
        'has_origin_safe_method_setter': any(
            method['is_check_security_for_frame'] and not method['is_read_only']
            for method in methods),
        'has_method_configuration': any(method['do_generate_method_configuration'] for method in methods),
        'has_per_context_enabled_methods': any(method['per_context_enabled_function'] for method in methods),
        'methods': methods,
    })

    native_entries = generate_native_entries(interface, constructors,
                                             custom_constructors, attributes,
                                             methods, named_constructor)

    template_contents.update({
        'indexed_property_getter': indexed_property_getter(interface),
        'indexed_property_setter': indexed_property_setter(interface),
        'indexed_property_deleter': indexed_property_deleter(interface),
        'is_override_builtins': 'OverrideBuiltins' in extended_attributes,
        'named_property_getter': named_property_getter(interface),
        'named_property_setter': named_property_setter(interface),
        'named_property_deleter': named_property_deleter(interface),
        'native_entries': native_entries,
    })

    return template_contents


def generate_native_entries(interface, constructors, custom_constructors,
                            attributes, methods, named_constructor):
    entries = []
    for constructor in constructors:
        entries.append(constructor['native_entry'])
    for constructor in custom_constructors:
        entries.append(constructor['native_entry'])
    if named_constructor:
        entries.append(named_constructor['native_entry'])
    for method in methods:
        entries.extend(method['native_entries'])
    for attribute in attributes:
        entries.append(attribute['native_entry_getter'])
        entries.append(attribute['native_entry_setter'])
    return entries


# [DeprecateAs], [Reflect], [RuntimeEnabled]
def generate_constant(constant):
    # (Blink-only) string literals are unquoted in tokenizer, must be re-quoted
    # in C++.
    if constant.idl_type.name == 'String':
        value = '"%s"' % constant.value
    else:
        value = constant.value

    extended_attributes = constant.extended_attributes
    return {
        'cpp_class': extended_attributes.get('PartialInterfaceImplementedAs'),
        'name': constant.name,
        # FIXME: use 'reflected_name' as correct 'name'
        'reflected_name': extended_attributes.get('Reflect', constant.name),
        'runtime_enabled_function': DartUtilities.runtime_enabled_function_name(constant),
        'value': value,
    }


################################################################################
# Overloads
################################################################################

def generate_method_native_entry(interface, method, count, optional_index):
    types = None
    if not method['is_custom']:
        types = [arg['preprocessed_type'] for arg in method['arguments'][0:count]]
    if method['is_call_with_script_arguments']:
        types.append("object")
    argument_names = [arg['name'] for arg in method['arguments'][0:count]]
    name = method['name']
    native_entry = \
        DartUtilities.generate_native_entry(interface.name, method,
                                            name, 'Method',
                                            optional_index,
                                            argument_names, types)
    return native_entry


def generate_method_native_entries(interface, methods):
    for method in methods:
        native_entries = []
        required_arg_count = method['number_of_required_arguments']
        arg_count = method['number_of_arguments']
        if required_arg_count != arg_count:
            for x in range(required_arg_count, arg_count + 1):
                # This is really silly, but is here for now just to match up
                # the existing name generation in the old dart:html scripts
                index = arg_count - x + 1
                native_entry = \
                    generate_method_native_entry(interface, method, x, index)
                native_entries.append(native_entry)
        else:
            # Eventually, we should probably always generate an unindexed
            # native entry, to handle cases like
            # addEventListener in which we suppress the optionality,
            # and in general to make us more robust against optional changes
            native_entry = \
                generate_method_native_entry(interface, method, arg_count, None)
            native_entries.append(native_entry)

        method.update({'native_entries': native_entries})

def generate_overloads(methods):
    generate_overloads_by_type(methods, is_static=False)  # Regular methods
    generate_overloads_by_type(methods, is_static=True)


def generate_overloads_by_type(methods, is_static):
    # Generates |overloads| template values and modifies |methods| in place;
    # |is_static| flag used (instead of partitioning list in 2) because need to
    # iterate over original list of methods to modify in place
    method_counts = defaultdict(lambda: 0)
    for method in methods:
        if method['is_static'] != is_static:
            continue
        name = method['name']
        # FIXME(vsm): We don't seem to capture optional param
        # overloads here.
        method_counts[name] += 1

    # Filter to only methods that are actually overloaded
    overloaded_method_counts = dict((name, count)
                                    for name, count in method_counts.iteritems()
                                    if count > 1)

    # Add overload information only to overloaded methods, so template code can
    # easily verify if a function is overloaded
    method_overloads = defaultdict(list)
    for method in methods:
        name = method['name']
        if (method['is_static'] != is_static or
            name not in overloaded_method_counts):
            continue
        # Overload index includes self, so first append, then compute index
        method_overloads[name].append(method)
        method.update({
            'overload_index': len(method_overloads[name]),
            'overload_resolution_expression': overload_resolution_expression(method),
        })
        # FIXME(vsm): Looks like we only handle optional parameters if
        # the method is already overloaded. For a non-overloaded method
        # with optional parameters, we never get here.

    # Resolution function is generated after last overloaded function;
    # package necessary information into |method.overloads| for that method.
    for method in methods:
        if (method['is_static'] != is_static or
            'overload_index' not in method):
            continue
        name = method['name']
        if method['overload_index'] != overloaded_method_counts[name]:
            continue
        overloads = method_overloads[name]
        minimum_number_of_required_arguments = min(
            overload['number_of_required_arguments']
            for overload in overloads)
        method['overloads'] = {
            'has_exception_state': bool(minimum_number_of_required_arguments),
            'methods': overloads,
            'minimum_number_of_required_arguments': minimum_number_of_required_arguments,
            'name': name,
        }


def overload_resolution_expression(method):
    # Expression is an OR of ANDs: each term in the OR corresponds to a
    # possible argument count for a given method, with type checks.
    # FIXME: Blink's overload resolution algorithm is incorrect, per:
    # Implement WebIDL overload resolution algorithm.
    # https://code.google.com/p/chromium/issues/detail?id=293561
    #
    # Currently if distinguishing non-primitive type from primitive type,
    # (e.g., sequence<DOMString> from DOMString or Dictionary from double)
    # the method with a non-primitive type argument must appear *first* in the
    # IDL file, since we're not adding a check to primitive types.
    # FIXME: Once fixed, check IDLs, as usually want methods with primitive
    # types to appear first (style-wise).
    #
    # Properly:
    # 1. Compute effective overload set.
    # 2. First check type list length.
    # 3. If multiple entries for given length, compute distinguishing argument
    #    index and have check for that type.
    arguments = method['arguments']
    overload_checks = [overload_check_expression(method, index)
                       # check *omitting* optional arguments at |index| and up:
                       # index 0 => argument_count 0 (no arguments)
                       # index 1 => argument_count 1 (index 0 argument only)
                       for index, argument in enumerate(arguments)
                       if argument['is_optional']]
    # FIXME: this is wrong if a method has optional arguments and a variadic
    # one, though there are not yet any examples of this
    if not method['is_variadic']:
        # Includes all optional arguments (len = last index + 1)
        overload_checks.append(overload_check_expression(method, len(arguments)))
    return ' || '.join('(%s)' % check for check in overload_checks)


def overload_check_expression(method, argument_count):
    overload_checks = ['info.Length() == %s' % argument_count]
    arguments = method['arguments'][:argument_count]
    overload_checks.extend(overload_check_argument(index, argument)
                           for index, argument in
                           enumerate(arguments))
    return ' && '.join('(%s)' % check for check in overload_checks if check)


def overload_check_argument(index, argument):
    def null_or_optional_check():
        # If undefined is passed for an optional argument, the argument should
        # be treated as missing; otherwise undefined is not allowed.

        # FIXME(vsm): We need Dart specific checks here.
        if idl_type.is_nullable:
            if argument['is_optional']:
                return 'isUndefinedOrNull(%s)'
            return '%s->IsNull()'
        if argument['is_optional']:
            return '%s->IsUndefined()'
        return None

    cpp_value = 'info[%s]' % index
    idl_type = argument['idl_type_object']
    # FIXME(vsm): We need Dart specific checks for the rest of this method.
    # FIXME: proper type checking, sharing code with attributes and methods
    # FIXME(terry): StrictTypeChecking no longer supported; TypeChecking is
    #               new extended attribute.
    if idl_type.name == 'String' and argument['is_strict_type_checking']:
        return ' || '.join(['isUndefinedOrNull(%s)' % cpp_value,
                            '%s->IsString()' % cpp_value,
                            '%s->IsObject()' % cpp_value])
    if idl_type.array_or_sequence_type:
        return '%s->IsArray()' % cpp_value
    if idl_type.is_callback_interface:
        return ' || '.join(['%s->IsNull()' % cpp_value,
                            '%s->IsFunction()' % cpp_value])
    if idl_type.is_wrapper_type:
        type_check = 'V8{idl_type}::hasInstance({cpp_value}, info.GetIsolate())'.format(idl_type=idl_type.base_type, cpp_value=cpp_value)
        if idl_type.is_nullable:
            type_check = ' || '.join(['%s->IsNull()' % cpp_value, type_check])
        return type_check
    if idl_type.is_interface_type:
        # Non-wrapper types are just objects: we don't distinguish type
        # We only allow undefined for non-wrapper types (notably Dictionary),
        # as we need it for optional Dictionary arguments, but we don't want to
        # change behavior of existing bindings for other types.
        type_check = '%s->IsObject()' % cpp_value
        added_check_template = null_or_optional_check()
        if added_check_template:
            type_check = ' || '.join([added_check_template % cpp_value,
                                      type_check])
        return type_check
    return None


################################################################################
# Constructors
################################################################################

# [Constructor]
def generate_custom_constructor(interface, constructor):
    return {
        'arguments': [custom_constructor_argument(argument, index)
                      for index, argument in enumerate(constructor.arguments)],
        'auto_scope': 'true',
        'is_auto_scope': True,
        'number_of_arguments': len(constructor.arguments),
        'number_of_required_arguments':
            number_of_required_arguments(constructor),
        }


# We don't need much from this - just the idl_type_objects and preproceed_type
# to use in generating the resolver strings.
def custom_constructor_argument(argument, index):
    return {
        'idl_type_object': argument.idl_type,
        'name': argument.name,
        'preprocessed_type': str(argument.idl_type.preprocessed_type),
    }


# [Constructor]
def generate_constructor(interface, constructor):
    return {
        'argument_list': constructor_argument_list(interface, constructor),
        # TODO(terry): Use dart_methods.generate_argument instead constructor_argument.
        'arguments': [constructor_argument(interface, argument, index)
                      for index, argument in enumerate(constructor.arguments)],
        'has_exception_state':
            # [RaisesException=Constructor]
            interface.extended_attributes.get('RaisesException') == 'Constructor' or
            any(argument for argument in constructor.arguments
                if argument.idl_type.name == 'SerializedScriptValue' or
                   argument.idl_type.is_integer_type),
        'is_constructor': True,
        'auto_scope': 'true',
        'is_auto_scope': True,
        'is_variadic': False,  # Required for overload resolution
        'number_of_required_arguments':
            number_of_required_arguments(constructor),
        'number_of_arguments': len(constructor.arguments),
    }


def constructor_argument_list(interface, constructor):
    # FIXME: unify with dart_methods.cpp_argument.

    def cpp_argument(argument):
        argument_name = dart_types.check_reserved_name(argument.name)
        idl_type = argument.idl_type
        if idl_type.is_typed_array_type:
            return '%s.get()' % argument_name

        return argument_name

    arguments = []
    # [ConstructorCallWith=ExecutionContext]
    if DartUtilities.has_extended_attribute_value(interface, 'ConstructorCallWith', 'ExecutionContext'):
        arguments.append('context')
    # [ConstructorCallWith=Document]
    if DartUtilities.has_extended_attribute_value(interface, 'ConstructorCallWith', 'Document'):
        arguments.append('document')

    arguments.extend([cpp_argument(argument) for argument in constructor.arguments])

    # [RaisesException=Constructor]
    if interface.extended_attributes.get('RaisesException') == 'Constructor':
        arguments.append('es')

    return arguments


# TODO(terry): Eliminate this function use dart_methods.generate_argument instead
#              for all constructor arguments.
def constructor_argument(interface, argument, index):
    idl_type = argument.idl_type
    default_value = str(argument.default_value) if argument.default_value else None

    argument_content = {
        'cpp_type': idl_type.cpp_type_args(),
        'local_cpp_type': idl_type.cpp_type_args(argument.extended_attributes, used_as_argument=True),
        # FIXME: check that the default value's type is compatible with the argument's
        'default_value': default_value,
        # FIXME: remove once [Default] removed and just use argument.default_value
        'has_default': 'Default' in argument.extended_attributes or default_value,
        'idl_type_object': idl_type,
        'preprocessed_type': str(idl_type.preprocessed_type),
        # Dictionary is special-cased, but arrays and sequences shouldn't be
        'idl_type': not idl_type.array_or_sequence_type and idl_type.base_type,
        'index': index,
        'is_array_or_sequence_type': not not idl_type.array_or_sequence_type,
        'is_optional': argument.is_optional,
        'is_strict_type_checking': False,  # Required for overload resolution
        'name': argument.name,
        'dart_value_to_local_cpp_value': dart_methods.dart_value_to_local_cpp_value(interface, argument, index),
    }
    return argument_content


def generate_constructor_overloads(constructors):
    if len(constructors) <= 1:
        return
    for overload_index, constructor in enumerate(constructors):
        constructor.update({
            'overload_index': overload_index + 1,
            'overload_resolution_expression':
                overload_resolution_expression(constructor),
        })


# [NamedConstructor]
def generate_named_constructor(interface):
    extended_attributes = interface.extended_attributes
    if 'NamedConstructor' not in extended_attributes:
        return None
    # FIXME: parser should return named constructor separately;
    # included in constructors (and only name stored in extended attribute)
    # for Perl compatibility
    idl_constructor = interface.constructors[0]
    constructor = generate_constructor(interface, idl_constructor)
    # FIXME(vsm): We drop the name. We don't use this in Dart APIs right now.
    # We probably need to encode this somehow to deal with conflicts.
    # constructor['name'] = extended_attributes['NamedConstructor']
    return constructor


def number_of_required_arguments(constructor):
    return len([argument for argument in constructor.arguments
        if not (argument.is_optional and not (('Default' in argument.extended_attributes) or argument.default_value))])


def interface_length(interface, constructors):
    # Docs: http://heycam.github.io/webidl/#es-interface-call
    if 'EventConstructor' in interface.extended_attributes:
        return 1
    if not constructors:
        return 0
    return min(constructor['number_of_required_arguments']
               for constructor in constructors)


################################################################################
# Special operations (methods)
# http://heycam.github.io/webidl/#idl-special-operations
################################################################################

def property_getter(getter, cpp_arguments):
    def is_null_expression(idl_type):
        if idl_type.is_union_type:
            return ' && '.join('!result%sEnabled' % i
                               for i, _ in enumerate(idl_type.member_types))
        if idl_type.name == 'String':
            # FIXME(vsm): This looks V8 specific.
            return 'result.isNull()'
        if idl_type.is_interface_type:
            return '!result'
        return ''

    idl_type = getter.idl_type
    extended_attributes = getter.extended_attributes
    is_raises_exception = 'RaisesException' in extended_attributes

    # FIXME: make more generic, so can use dart_methods.cpp_value
    cpp_method_name = 'receiver->%s' % DartUtilities.cpp_name(getter)

    if is_raises_exception:
        cpp_arguments.append('es')
    union_arguments = idl_type.union_arguments
    if union_arguments:
        cpp_arguments.extend(union_arguments)

    cpp_value = '%s(%s)' % (cpp_method_name, ', '.join(cpp_arguments))

    return {
        'cpp_type': idl_type.cpp_type,
        'cpp_value': cpp_value,
        'is_custom':
            'Custom' in extended_attributes and
            (not extended_attributes['Custom'] or
             DartUtilities.has_extended_attribute_value(getter, 'Custom', 'PropertyGetter')),
        'is_custom_property_enumerator': DartUtilities.has_extended_attribute_value(
            getter, 'Custom', 'PropertyEnumerator'),
        'is_custom_property_query': DartUtilities.has_extended_attribute_value(
            getter, 'Custom', 'PropertyQuery'),
        'is_enumerable': 'NotEnumerable' not in extended_attributes,
        'is_null_expression': is_null_expression(idl_type),
        'is_raises_exception': is_raises_exception,
        'name': DartUtilities.cpp_name(getter),
        'union_arguments': union_arguments,
        'dart_set_return_value': idl_type.dart_set_return_value('result',
                                                                extended_attributes=extended_attributes,
                                                                script_wrappable='receiver',
                                                                release=idl_type.release)}


def property_setter(interface, setter):
    idl_type = setter.arguments[1].idl_type
    extended_attributes = setter.extended_attributes
    interface_extended_attributes = interface.extended_attributes
    is_raises_exception = 'RaisesException' in extended_attributes
    return {
        'has_strict_type_checking':
            'StrictTypeChecking' in extended_attributes and
            idl_type.is_wrapper_type,
        'idl_type': idl_type.base_type,
        'is_custom': 'Custom' in extended_attributes,
        'has_exception_state': is_raises_exception or
                               idl_type.is_integer_type,
        'is_raises_exception': is_raises_exception,
        'name': DartUtilities.cpp_name(setter),
        'dart_value_to_local_cpp_value': idl_type.dart_value_to_local_cpp_value(
            interface_extended_attributes, extended_attributes, 'propertyValue', False),
    }


def property_deleter(deleter):
    idl_type = deleter.idl_type
    if str(idl_type) != 'boolean':
        raise Exception(
            'Only deleters with boolean type are allowed, but type is "%s"' %
            idl_type)
    extended_attributes = deleter.extended_attributes
    return {
        'is_custom': 'Custom' in extended_attributes,
        'is_raises_exception': 'RaisesException' in extended_attributes,
        'name': DartUtilities.cpp_name(deleter),
    }


################################################################################
# Indexed properties
# http://heycam.github.io/webidl/#idl-indexed-properties
################################################################################

def indexed_property_getter(interface):
    try:
        # Find indexed property getter, if present; has form:
        # getter TYPE [OPTIONAL_IDENTIFIER](unsigned long ARG1)
        getter = next(
            method
            for method in interface.operations
            if ('getter' in method.specials and
                len(method.arguments) == 1 and
                str(method.arguments[0].idl_type) == 'unsigned long'))
    except StopIteration:
        return None

    getter.name = getter.name or 'anonymousIndexedGetter'

    return property_getter(getter, ['index'])


def indexed_property_setter(interface):
    try:
        # Find indexed property setter, if present; has form:
        # setter RETURN_TYPE [OPTIONAL_IDENTIFIER](unsigned long ARG1, ARG_TYPE ARG2)
        setter = next(
            method
            for method in interface.operations
            if ('setter' in method.specials and
                len(method.arguments) == 2 and
                str(method.arguments[0].idl_type) == 'unsigned long'))
    except StopIteration:
        return None

    return property_setter(interface, setter)


def indexed_property_deleter(interface):
    try:
        # Find indexed property deleter, if present; has form:
        # deleter TYPE [OPTIONAL_IDENTIFIER](unsigned long ARG)
        deleter = next(
            method
            for method in interface.operations
            if ('deleter' in method.specials and
                len(method.arguments) == 1 and
                str(method.arguments[0].idl_type) == 'unsigned long'))
    except StopIteration:
        return None

    return property_deleter(deleter)


################################################################################
# Named properties
# http://heycam.github.io/webidl/#idl-named-properties
################################################################################

def named_property_getter(interface):
    try:
        # Find named property getter, if present; has form:
        # getter TYPE [OPTIONAL_IDENTIFIER](DOMString ARG1)
        getter = next(
            method
            for method in interface.operations
            if ('getter' in method.specials and
                len(method.arguments) == 1 and
                str(method.arguments[0].idl_type) == 'DOMString'))
    except StopIteration:
        return None

    getter.name = getter.name or 'anonymousNamedGetter'
    return property_getter(getter, ['propertyName'])


def named_property_setter(interface):
    try:
        # Find named property setter, if present; has form:
        # setter RETURN_TYPE [OPTIONAL_IDENTIFIER](DOMString ARG1, ARG_TYPE ARG2)
        setter = next(
            method
            for method in interface.operations
            if ('setter' in method.specials and
                len(method.arguments) == 2 and
                str(method.arguments[0].idl_type) == 'DOMString'))
    except StopIteration:
        return None

    return property_setter(interface, setter)


def named_property_deleter(interface):
    try:
        # Find named property deleter, if present; has form:
        # deleter TYPE [OPTIONAL_IDENTIFIER](DOMString ARG)
        deleter = next(
            method
            for method in interface.operations
            if ('deleter' in method.specials and
                len(method.arguments) == 1 and
                str(method.arguments[0].idl_type) == 'DOMString'))
    except StopIteration:
        return None

    return property_deleter(deleter)
