export interface Interest {
  id: string;
  name: string;
  related_terms: string;
  status: "published" | "draft";
  color: string;
  created_at: string;
}
export interface InterestData {
  name: string;
  related_terms: string;
  status: "published" | "draft";
  color: string;
}
