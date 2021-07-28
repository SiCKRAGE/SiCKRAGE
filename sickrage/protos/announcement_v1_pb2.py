# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: announcement_v1.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='announcement_v1.proto',
  package='app.protobufs.v1',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x15\x61nnouncement_v1.proto\x12\x10\x61pp.protobufs.v1\"m\n\x1b\x43reatedAnnouncementResponse\x12\r\n\x05\x61hash\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\x12\r\n\x05image\x18\x04 \x01(\t\x12\x0c\n\x04\x64\x61te\x18\x05 \x01(\t\",\n\x1b\x44\x65letedAnnouncementResponse\x12\r\n\x05\x61hash\x18\x01 \x01(\tb\x06proto3'
)




_CREATEDANNOUNCEMENTRESPONSE = _descriptor.Descriptor(
  name='CreatedAnnouncementResponse',
  full_name='app.protobufs.v1.CreatedAnnouncementResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='ahash', full_name='app.protobufs.v1.CreatedAnnouncementResponse.ahash', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='title', full_name='app.protobufs.v1.CreatedAnnouncementResponse.title', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='description', full_name='app.protobufs.v1.CreatedAnnouncementResponse.description', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='image', full_name='app.protobufs.v1.CreatedAnnouncementResponse.image', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='date', full_name='app.protobufs.v1.CreatedAnnouncementResponse.date', index=4,
      number=5, type=9, cpp_type=9, label=1,
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
  serialized_start=43,
  serialized_end=152,
)


_DELETEDANNOUNCEMENTRESPONSE = _descriptor.Descriptor(
  name='DeletedAnnouncementResponse',
  full_name='app.protobufs.v1.DeletedAnnouncementResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='ahash', full_name='app.protobufs.v1.DeletedAnnouncementResponse.ahash', index=0,
      number=1, type=9, cpp_type=9, label=1,
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
  serialized_start=154,
  serialized_end=198,
)

DESCRIPTOR.message_types_by_name['CreatedAnnouncementResponse'] = _CREATEDANNOUNCEMENTRESPONSE
DESCRIPTOR.message_types_by_name['DeletedAnnouncementResponse'] = _DELETEDANNOUNCEMENTRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

CreatedAnnouncementResponse = _reflection.GeneratedProtocolMessageType('CreatedAnnouncementResponse', (_message.Message,), {
  'DESCRIPTOR' : _CREATEDANNOUNCEMENTRESPONSE,
  '__module__' : 'announcement_v1_pb2'
  # @@protoc_insertion_point(class_scope:app.protobufs.v1.CreatedAnnouncementResponse)
  })
_sym_db.RegisterMessage(CreatedAnnouncementResponse)

DeletedAnnouncementResponse = _reflection.GeneratedProtocolMessageType('DeletedAnnouncementResponse', (_message.Message,), {
  'DESCRIPTOR' : _DELETEDANNOUNCEMENTRESPONSE,
  '__module__' : 'announcement_v1_pb2'
  # @@protoc_insertion_point(class_scope:app.protobufs.v1.DeletedAnnouncementResponse)
  })
_sym_db.RegisterMessage(DeletedAnnouncementResponse)


# @@protoc_insertion_point(module_scope)
