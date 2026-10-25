export type NiveauRisque = 'faible' | 'moyen' | 'eleve' | 'tres_eleve';

export interface RapportVerification {
  id: number;
  score_credibilite: number;
  niveau_risque: NiveauRisque;
  niveau_risque_libelle: string;
  resume: string;
  recommandations: string[];
  genere_le: string;
  fichier_pdf: string | null;
  fichier_image: string | null;
}

export interface ReponseRapportGenere {
  message: string;
  rapport: RapportVerification;
}
