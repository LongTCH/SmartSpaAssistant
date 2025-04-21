export interface Script {
  id: string;
  name: string;
  description: string;
  solution: string;
  status: "published" | "draft";
  created_at: string;
}
export interface ScriptData {
  name: string;
  description: string;
  solution: string;
  status: "published" | "draft";
}
