import { Injectable } from '@angular/core';

/**
 * Centralise le stockage local des jetons JWT.
 *
 * Ce service ne dépend pas de HttpClient : l'intercepteur peut l'utiliser
 * sans créer de dépendance circulaire avec le service d'authentification.
 */
@Injectable({ providedIn: 'root' })
export class ServiceJetons {
  private readonly cleJetonAcces = 'factcheck.jeton_acces';
  private readonly cleJetonRafraichissement = 'factcheck.jeton_rafraichissement';

  obtenirJetonAcces(): string | null {
    return this.lire(this.cleJetonAcces);
  }

  obtenirJetonRafraichissement(): string | null {
    return this.lire(this.cleJetonRafraichissement);
  }

  enregistrerJetons(jetonAcces: string, jetonRafraichissement: string): void {
    this.ecrire(this.cleJetonAcces, jetonAcces);
    this.ecrire(this.cleJetonRafraichissement, jetonRafraichissement);
  }

  enregistrerJetonAcces(jetonAcces: string): void {
    this.ecrire(this.cleJetonAcces, jetonAcces);
  }

  supprimerJetons(): void {
    this.supprimer(this.cleJetonAcces);
    this.supprimer(this.cleJetonRafraichissement);
  }

  aUnJetonAcces(): boolean {
    return Boolean(this.obtenirJetonAcces());
  }

  private lire(cle: string): string | null {
    if (typeof localStorage === 'undefined') {
      return null;
    }
    return localStorage.getItem(cle);
  }

  private ecrire(cle: string, valeur: string): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(cle, valeur);
    }
  }

  private supprimer(cle: string): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(cle);
    }
  }
}
