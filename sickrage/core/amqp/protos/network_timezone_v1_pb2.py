# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: network_timezone_v1.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x19network_timezone_v1.proto\x12\x10\x61pp.protobufs.v1\"A\n\x1cSavedNetworkTimezoneResponse\x12\x0f\n\x07network\x18\x01 \x01(\t\x12\x10\n\x08timezone\x18\x02 \x01(\t\"1\n\x1e\x44\x65letedNetworkTimezoneResponse\x12\x0f\n\x07network\x18\x01 \x01(\tb\x06proto3')



_SAVEDNETWORKTIMEZONERESPONSE = DESCRIPTOR.message_types_by_name['SavedNetworkTimezoneResponse']
_DELETEDNETWORKTIMEZONERESPONSE = DESCRIPTOR.message_types_by_name['DeletedNetworkTimezoneResponse']
SavedNetworkTimezoneResponse = _reflection.GeneratedProtocolMessageType('SavedNetworkTimezoneResponse', (_message.Message,), {
  'DESCRIPTOR' : _SAVEDNETWORKTIMEZONERESPONSE,
  '__module__' : 'network_timezone_v1_pb2'
  # @@protoc_insertion_point(class_scope:app.protobufs.v1.SavedNetworkTimezoneResponse)
  })
_sym_db.RegisterMessage(SavedNetworkTimezoneResponse)

DeletedNetworkTimezoneResponse = _reflection.GeneratedProtocolMessageType('DeletedNetworkTimezoneResponse', (_message.Message,), {
  'DESCRIPTOR' : _DELETEDNETWORKTIMEZONERESPONSE,
  '__module__' : 'network_timezone_v1_pb2'
  # @@protoc_insertion_point(class_scope:app.protobufs.v1.DeletedNetworkTimezoneResponse)
  })
_sym_db.RegisterMessage(DeletedNetworkTimezoneResponse)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _SAVEDNETWORKTIMEZONERESPONSE._serialized_start=47
  _SAVEDNETWORKTIMEZONERESPONSE._serialized_end=112
  _DELETEDNETWORKTIMEZONERESPONSE._serialized_start=114
  _DELETEDNETWORKTIMEZONERESPONSE._serialized_end=163
# @@protoc_insertion_point(module_scope)
