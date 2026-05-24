-- Migration 039: associes nb_parts migration
-- Migrate parts from percentages to integers

-- First ensure sci has default for nb_parts_total if null
UPDATE sci SET nb_parts_total = 1000 WHERE nb_parts_total IS NULL;

-- Migrate associes parts to nb_parts if null
UPDATE associes a
SET nb_parts = ROUND((a.part / 100.0) * s.nb_parts_total)::integer
FROM sci s
WHERE a.id_sci = s.id AND a.nb_parts IS NULL;

-- If still null, default to 500
UPDATE associes SET nb_parts = 500 WHERE nb_parts IS NULL;

-- Make nb_parts NOT NULL
ALTER TABLE associes ALTER COLUMN nb_parts SET NOT NULL;
