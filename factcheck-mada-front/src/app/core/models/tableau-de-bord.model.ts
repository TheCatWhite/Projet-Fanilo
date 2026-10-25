import { RumeurListe } from './rumeur.model';

export interface StatistiquesTableauDeBord {
  total_rumeurs: number;
  rumeurs_analysees: number;
  rumeurs_haut_risque: number;
  total_publications: number;
  plateforme_plus_active: string | null;
  repartition_plateformes: Record<string, number>;
  rumeurs_recentes: RumeurListe[];
}
