export interface Script {
  id: string;
  name: string;
  description: string;
  solution: string;
  status: "published" | "draft";
  created_at: string;
  related_scripts?: Script[];
}
export interface ScriptData {
  name: string;
  description: string;
  solution: string;
  status: "published" | "draft";
  related_script_ids: string[];
}
