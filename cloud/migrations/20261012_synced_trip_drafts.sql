-- Saved drafts may omit identifiers and measurements; populated values remain validated.
ALTER TABLE public.ysk_trips DROP CONSTRAINT payload_shape;
ALTER TABLE public.ysk_trips ADD CONSTRAINT payload_shape CHECK (coalesce(
jsonb_typeof(payload)='object'
AND payload ?& ARRAY['id','driver','course','vehicle','trip','minutes','km','liters','stops','trafikksikkerhet','avpassing','økning','komfort']
AND payload->>'id'=id::text AND payload->>'driver'=driver AND payload->>'course'=course AND payload->>'vehicle'=vehicle
AND CASE WHEN jsonb_typeof(payload->'trip')='number' THEN (payload->>'trip')::numeric=trip ELSE false END
AND (CASE WHEN payload->>'minutes' IN ('-', '') THEN true WHEN jsonb_typeof(payload->'minutes') = 'number' THEN (payload->>'minutes')::numeric > 0  ELSE false END)
 AND (CASE WHEN payload->>'km' IN ('-', '') THEN true WHEN jsonb_typeof(payload->'km') = 'number' THEN (payload->>'km')::numeric > 0  ELSE false END)
 AND (CASE WHEN payload->>'liters' IN ('-', '') THEN true WHEN jsonb_typeof(payload->'liters') = 'number' THEN (payload->>'liters')::numeric >= 0  ELSE false END)
 AND (CASE WHEN payload->>'stops' IN ('-', '') THEN true WHEN jsonb_typeof(payload->'stops') = 'number' THEN (payload->>'stops')::numeric >= 0 AND (payload->>'stops')::numeric = trunc((payload->>'stops')::numeric) ELSE false END)
AND payload->>'trafikksikkerhet' IN ('Bra','Middel','Svak','-','') AND payload->>'avpassing' IN ('Bra','Middel','Svak','-','') AND payload->>'økning' IN ('Bra','Middel','Svak','-','') AND payload->>'komfort' IN ('Bra','Middel','Svak','-','')
AND (NOT payload ? 'notes' OR (jsonb_typeof(payload->'notes')='string' AND length(payload->>'notes')<=2000)),false));
ALTER TABLE public.ysk_trips DROP CONSTRAINT ysk_trips_driver_check;
ALTER TABLE public.ysk_trips ADD CONSTRAINT ysk_trips_driver_check CHECK (length(driver)<=100 AND driver=btrim(driver));
ALTER TABLE public.ysk_trips DROP CONSTRAINT ysk_trips_course_check;
ALTER TABLE public.ysk_trips ADD CONSTRAINT ysk_trips_course_check CHECK (length(course)<=100 AND course=btrim(course));
ALTER TABLE public.ysk_trips DROP CONSTRAINT ysk_trips_vehicle_check;
ALTER TABLE public.ysk_trips ADD CONSTRAINT ysk_trips_vehicle_check CHECK (length(vehicle)<=100 AND vehicle=btrim(vehicle));
DROP INDEX public.ysk_active_class_trip;
CREATE UNIQUE INDEX ysk_active_class_trip ON public.ysk_trips(organization_id,driver,course,vehicle,trip) WHERE deleted_at IS NULL AND driver<>'' AND course<>'' AND vehicle<>'';
DROP INDEX public.ysk_active_owner_trip;
CREATE UNIQUE INDEX ysk_active_owner_trip ON public.ysk_trips(owner_id,driver,course,vehicle,trip) WHERE deleted_at IS NULL AND driver<>'' AND course<>'' AND vehicle<>'';
