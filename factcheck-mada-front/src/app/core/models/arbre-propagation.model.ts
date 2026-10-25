export interface NoeudPropagation {
  id: number;
  plateforme: string;
  plateforme_libelle: string;
  nom_auteur: string;
  url_publication: string;
  date_publication: string;
  est_premiere_detection: boolean;
  indicateurs_risque: string[];
  nombre_alertes: number;
}

export interface LienArbre {
  publication_parent_id: number | null;
  publication_enfant_id: number;
  score_similarite: number;
}

export interface StatistiquesPropagation {
  nombre_publications: number;
  plateformes: string[];
  premiere_publication: string | null;
  derniere_publication: string | null;
  vitesse_estimee: string;
  duree_heures: number;
  repartition_plateformes: Record<string, number>;
}

export interface ArbrePropagation {
  rumeur_id: number;
  premiere_publication_detectee: NoeudPropagation | null;
  noeuds: NoeudPropagation[];
  liens: LienArbre[];
  statistiques_propagation: StatistiquesPropagation;
}
