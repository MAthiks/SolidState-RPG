class EndpointBindingGate:
 @staticmethod
 def bind(role_marker,entity_ref,authority):
  if role_marker not in ("START","TERMINAL"):return {"status":"BLOCKED","code":"INVALID_ROLE"}
  if not entity_ref:return {"status":"BLOCKED","code":"ENTITY_REF_REQUIRED"}
  if authority not in ("EXPLICIT_HEADING_BINDING","EXPLICIT_LITERAL_BINDING","EXPLICIT_TERMINAL_MARKER_BINDING"):return {"status":"BLOCKED","code":"BINDING_AUTHORITY_INSUFFICIENT"}
  return {"status":"BOUND","role":role_marker,"entity_ref":entity_ref,"authority":authority}
