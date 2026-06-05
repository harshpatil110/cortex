-- Supabase Storage Setup & RLS Policies for Cortex

-- 1. Create Private Buckets
INSERT INTO storage.buckets (id, name, public) VALUES ('raw-media', 'raw-media', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('thumbnails', 'thumbnails', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('pdfs', 'pdfs', false);
INSERT INTO storage.buckets (id, name, public) VALUES ('screenshots', 'screenshots', false);

-- 2. Enable RLS on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies for 'raw-media'
-- Authenticated users can insert their own raw-media
CREATE POLICY "Users can upload their own raw-media" ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'raw-media' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Authenticated users can view their own raw-media
CREATE POLICY "Users can view their own raw-media" ON storage.objects
FOR SELECT TO authenticated
USING (bucket_id = 'raw-media' AND (storage.foldername(name))[1] = auth.uid()::text);

-- Authenticated users can update/delete their own raw-media
CREATE POLICY "Users can update their own raw-media" ON storage.objects
FOR UPDATE TO authenticated
USING (bucket_id = 'raw-media' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can delete their own raw-media" ON storage.objects
FOR DELETE TO authenticated
USING (bucket_id = 'raw-media' AND (storage.foldername(name))[1] = auth.uid()::text);

-- 4. RLS Policies for 'thumbnails'
CREATE POLICY "Users can upload their own thumbnails" ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'thumbnails' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can view their own thumbnails" ON storage.objects
FOR SELECT TO authenticated
USING (bucket_id = 'thumbnails' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can update their own thumbnails" ON storage.objects
FOR UPDATE TO authenticated
USING (bucket_id = 'thumbnails' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can delete their own thumbnails" ON storage.objects
FOR DELETE TO authenticated
USING (bucket_id = 'thumbnails' AND (storage.foldername(name))[1] = auth.uid()::text);

-- 5. RLS Policies for 'pdfs'
CREATE POLICY "Users can upload their own pdfs" ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'pdfs' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can view their own pdfs" ON storage.objects
FOR SELECT TO authenticated
USING (bucket_id = 'pdfs' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can update their own pdfs" ON storage.objects
FOR UPDATE TO authenticated
USING (bucket_id = 'pdfs' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can delete their own pdfs" ON storage.objects
FOR DELETE TO authenticated
USING (bucket_id = 'pdfs' AND (storage.foldername(name))[1] = auth.uid()::text);

-- 6. RLS Policies for 'screenshots'
CREATE POLICY "Users can upload their own screenshots" ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'screenshots' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can view their own screenshots" ON storage.objects
FOR SELECT TO authenticated
USING (bucket_id = 'screenshots' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can update their own screenshots" ON storage.objects
FOR UPDATE TO authenticated
USING (bucket_id = 'screenshots' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can delete their own screenshots" ON storage.objects
FOR DELETE TO authenticated
USING (bucket_id = 'screenshots' AND (storage.foldername(name))[1] = auth.uid()::text);
