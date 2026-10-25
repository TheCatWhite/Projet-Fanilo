export type RoleJournaliste = 'journaliste' | 'redacteur_en_chef' | 'administrateur';

export interface Journaliste {
  id: number;
  nom_utilisateur: string;
  email: string;
  redaction: string;
  role: RoleJournaliste;
  date_inscription: string;
  est_administrateur: boolean;
}

export const LIBELLES_ROLE: Record<RoleJournaliste, string> = {
  journaliste: 'Journaliste',
  redacteur_en_chef: 'Rédacteur en chef',
  administrateur: 'Administrateur',
};
