import { AlerteCompte } from './alerte-compte.model';
import { AlerteTexte } from './alerte-texte.model';

export interface AnalyseTexte {
  rumeur_id: number;
  score_risque_texte: number;
  nombre_alertes: number;
  alertes: AlerteTexte[];
}

export interface AnalyseCompte {
  publication_id: number;
  nombre_alertes: number;
  alertes: AlerteCompte[];
  message: string;
}
