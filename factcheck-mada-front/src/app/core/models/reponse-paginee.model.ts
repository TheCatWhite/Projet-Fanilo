export interface ReponsePaginee<T> {
  total: number;
  suivant: string | null;
  precedent: string | null;
  resultats: T[];
}
