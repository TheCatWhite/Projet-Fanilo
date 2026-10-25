import { Journaliste } from './journaliste.model';

export interface IdentifiantsConnexion {
  nom_utilisateur: string;
  mot_de_passe: string;
}

export interface DonneesInscription {
  nom_utilisateur: string;
  email: string;
  mot_de_passe: string;
  confirmation_mot_de_passe: string;
  redaction?: string;
}

export interface ReponseAuthentification {
  message: string;
  journaliste: Journaliste;
  jeton_acces: string;
  jeton_rafraichissement: string;
}

export interface DonneesRafraichissement {
  jeton_rafraichissement: string;
}

export interface ReponseRafraichissement {
  jeton_acces: string;
  message: string;
}
