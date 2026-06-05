CREATE TABLE memory_plates (
    memory_id UUID REFERENCES user_memories(id) ON DELETE CASCADE,
    plate_id UUID REFERENCES plates(id) ON DELETE CASCADE,
    PRIMARY KEY (memory_id, plate_id)
);

-- RLS
ALTER TABLE memory_plates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own memory plates" ON memory_plates FOR ALL USING (
    EXISTS (SELECT 1 FROM plates WHERE id = memory_plates.plate_id AND user_id = auth.uid())
);
