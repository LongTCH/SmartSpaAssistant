CREATE EXTENSION IF NOT EXISTS pgroonga;

CREATE INDEX IF NOT EXISTS pgroonga_sheet_row_data_index ON sheet_rows USING pgroonga (data);
