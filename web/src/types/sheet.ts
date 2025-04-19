export interface ExcelData {
  headers: string[];
  rows: any[][];
}

export interface Sheet {
  id: string;
  name: string;
  description: string;
  schema: string[];
  status: "published" | "draft";
  created_at: string;
}

export interface SheetRow {
  [key: string]: string;
}
