export interface LienPropagation {
  id: number;
  publication_parent_id: number | null;
  publication_enfant_id: number;
  score_similarite: number;
  detecte_le: string;
}
