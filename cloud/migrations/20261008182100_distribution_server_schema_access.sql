-- Course/trip constraints call validators in the private schema.
-- Grant only the trusted server role name resolution; keep client access unchanged.
grant usage on schema ysk_private to service_role;
