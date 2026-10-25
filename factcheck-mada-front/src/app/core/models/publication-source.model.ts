import { AlerteCompte } from './alerte-compte.model';

export type Plateforme =
  'facebook' | 'messenger' | 'whatsapp' | 'tiktok' | 'youtube' | 'site_web' | 'autre';

export const LIBELLES_PLATEFORME: Record<Plateforme, string> = {
  facebook: 'Facebook',
  messenger: 'Messenger',
  whatsapp: 'WhatsApp',
  tiktok: 'TikTok',
  youtube: 'YouTube',
  site_web: 'Site web',
  autre: 'Autre',
};

export const ICONES_PLATEFORME: Record<Plateforme, string> = {
  facebook: 'f',
  messenger: 'm',
  whatsapp: 'W',
  tiktok: 'T',
  youtube: '▶',
  site_web: '⌘',
  autre: '•',
};

export interface PublicationSource {
  id: number;
  rumeur: number;
  plateforme: Plateforme;
  plateforme_libelle: string;
  url_publication: string;
  nom_auteur: string;
  url_profil_auteur: string;
  date_creation_compte: string | null;
  nombre_abonnes: number | null;
  date_publication: string;
  est_premiere_detection: boolean;
  texte_brut: string;
  capture_ecran: string | null;
  cree_le: string;
  alertes_compte: AlerteCompte[];
}

export interface DonneesPublication {
  plateforme: Plateforme;
  url_publication?: string;
  nom_auteur: string;
  url_profil_auteur?: string;
  date_creation_compte?: string;
  nombre_abonnes?: number | null;
  date_publication: string;
  texte_brut?: string;
  capture_ecran?: File | null;
}

export interface ReponseCreationPublication {
  message: string;
  publication: PublicationSource;
  liens_crees: import('./lien-propagation.model').LienPropagation[];
  alertes_compte: AlerteCompte[];
  analyse_texte: {
    score_risque_texte: number;
    nombre_alertes: number;
    alertes: import('./alerte-texte.model').AlerteTexte[];
  };
  premiere_publication_detectee: PublicationSource | null;
}
