import { AlerteTexte } from './alerte-texte.model';
import { LienPropagation } from './lien-propagation.model';
import { NiveauRisque, RapportVerification } from './rapport-verification.model';
import { PublicationSource } from './publication-source.model';

export type StatutRumeur = 'en_analyse' | 'analyse_terminee' | 'archivee';
export type LangueRumeur = 'fr' | 'mg' | 'en' | 'autre';

export const LIBELLES_STATUT: Record<StatutRumeur, string> = {
  en_analyse: 'En analyse',
  analyse_terminee: 'Analyse terminée',
  archivee: 'Archivée',
};

export const LIBELLES_LANGUE: Record<LangueRumeur, string> = {
  fr: 'Français',
  mg: 'Malagasy',
  en: 'Anglais',
  autre: 'Autre',
};

export interface RumeurListe {
  id: number;
  titre: string;
  extrait_contenu: string;
  langue: LangueRumeur;
  langue_libelle: string;
  statut: StatutRumeur;
  statut_libelle: string;
  empreinte_contenu: string;
  cree_le: string;
  nombre_publications: number;
  score_credibilite: number | null;
  niveau_risque: NiveauRisque | null;
  niveau_risque_libelle: string | null;
}

export interface RumeurDetail extends RumeurListe {
  contenu: string;
  cree_par: number;
  cree_par_nom: string;
  publications: PublicationSource[];
  alertes_texte: AlerteTexte[];
  liens_propagation: LienPropagation[];
  rapport: RapportVerification | null;
}

export interface RumeurSimilaire {
  id: number;
  titre: string;
  score_similarite: number;
  cree_le: string;
  statut: string;
}

export interface ReponseCreationRumeur {
  cree: boolean;
  message: string;
  rumeur: RumeurDetail;
  similaires: RumeurSimilaire[];
}

export interface DonneesCreationRumeur {
  titre: string;
  contenu: string;
  langue: LangueRumeur;
}

export interface DonneesModificationRumeur {
  titre?: string;
  contenu?: string;
  statut?: StatutRumeur;
}

export interface FiltresRumeurs {
  page?: number;
  taille_page?: number;
  statut?: StatutRumeur | '';
  titre?: string;
  recherche?: string;
  date_debut?: string;
  date_fin?: string;
  tri?: string;
}
