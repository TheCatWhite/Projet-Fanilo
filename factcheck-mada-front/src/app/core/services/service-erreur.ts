import { HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';

/**
 * Transforme les erreurs Django REST Framework en messages lisibles.
 *
 * Le backend renvoie soit un champ « detail », soit un dictionnaire de champs
 * avec des tableaux de messages de validation.
 */
@Injectable({ providedIn: 'root' })
export class ServiceErreur {
  extraireMessages(erreur: unknown): string[] {
    if (erreur instanceof HttpErrorResponse) {
      if (erreur.status === 0) {
        return [
          'Impossible de joindre le serveur Django. Vérifiez qu’il est lancé sur http://localhost:8000.',
        ];
      }

      if (erreur.status === 401) {
        return ['Votre session a expiré. Veuillez vous reconnecter.'];
      }

      if (erreur.status === 403) {
        return ['Vous n’avez pas les droits nécessaires pour effectuer cette action.'];
      }

      if (erreur.status === 404) {
        return ['La ressource demandée est introuvable ou ne vous appartient pas.'];
      }

      if (erreur.status === 501) {
        return [
          'Cette fonctionnalité n’est pas disponible sur le serveur (bibliothèque manquante).',
        ];
      }

      return this.lireCorps(erreur.error, erreur.status);
    }

    if (typeof erreur === 'string') {
      return [erreur];
    }

    if (erreur instanceof Error && erreur.message) {
      return [erreur.message];
    }

    return ['Une erreur inattendue est survenue. Veuillez réessayer.'];
  }

  extraireMessage(erreur: unknown): string {
    return this.extraireMessages(erreur).join(' ');
  }

  private lireCorps(corps: unknown, statut: number): string[] {
    if (typeof corps === 'string' && corps.trim()) {
      return [corps];
    }

    if (this.estObjet(corps)) {
      const detail = corps['detail'];
      if (typeof detail === 'string' && detail.trim()) {
        return [detail];
      }

      const messages: string[] = [];
      for (const [champ, valeur] of Object.entries(corps)) {
        const textes = this.lireValeur(valeur);
        for (const texte of textes) {
          messages.push(champ === 'non_field_errors' ? texte : `${champ} : ${texte}`);
        }
      }
      if (messages.length > 0) {
        return messages;
      }
    }

    return [`Erreur ${statut} lors de l’appel au serveur.`];
  }

  private lireValeur(valeur: unknown): string[] {
    if (typeof valeur === 'string') {
      return [valeur];
    }
    if (Array.isArray(valeur)) {
      return valeur.flatMap((element) => this.lireValeur(element));
    }
    if (this.estObjet(valeur)) {
      return Object.values(valeur).flatMap((element) => this.lireValeur(element));
    }
    return [];
  }

  private estObjet(valeur: unknown): valeur is Record<string, unknown> {
    return typeof valeur === 'object' && valeur !== null && !Array.isArray(valeur);
  }
}
