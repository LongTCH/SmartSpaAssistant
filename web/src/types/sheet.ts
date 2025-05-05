export interface ExcelData {
  headers: string[];
  rows: any[][];
}

export interface Sheet {
  id: string;
  name: string;
  description: string;
  column_config: Array<ColumnConfig>;
  status: "published" | "draft";
  created_at: string;
}

export interface SheetRow {
  [key: string]: string;
}

export type ColumnType =
  | "String"
  | "Integer"
  | "Numeric"
  | "DateTime"
  | "Boolean"
  | "Text";

export interface ColumnConfig {
  column_name: string;
  description?: string;
  column_type: ColumnType;
  is_index: boolean;
}
