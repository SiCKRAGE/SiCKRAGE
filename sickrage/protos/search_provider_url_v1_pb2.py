# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: search_provider_url_v1.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='search_provider_url_v1.proto',
  package='app.protobufs.v1',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x1csearch_provider_url_v1.proto\x12\x10\x61pp.protobufs.v1\"L\n\x1eSavedSearchProviderUrlResponse\x12\x13\n\x0bprovider_id\x18\x01 \x01(\t\x12\x15\n\rprovider_urls\x18\x02 \x01(\tb\x06proto3'
)




_SAVEDSEARCHPROVIDERURLRESPONSE = _descriptor.Descriptor(
  name='SavedSearchProviderUrlResponse',
  full_name='app.protobufs.v1.SavedSearchProviderUrlResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='provider_id', full_name='app.protobufs.v1.SavedSearchProviderUrlResponse.provider_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='provider_urls', full_name='app.protobufs.v1.SavedSearchProviderUrlResponse.provider_urls', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=50,
  serialized_end=126,
)

DESCRIPTOR.message_types_by_name['SavedSearchProviderUrlResponse'] = _SAVEDSEARCHPROVIDERURLRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

SavedSearchProviderUrlResponse = _reflection.GeneratedProtocolMessageType('SavedSearchProviderUrlResponse', (_message.Message,), {
  'DESCRIPTOR' : _SAVEDSEARCHPROVIDERURLRESPONSE,
  '__module__' : 'search_provider_url_v1_pb2'
  # @@protoc_insertion_point(class_scope:app.protobufs.v1.SavedSearchProviderUrlResponse)
  })
_sym_db.RegisterMessage(SavedSearchProviderUrlResponse)


# @@protoc_insertion_point(module_scope)
