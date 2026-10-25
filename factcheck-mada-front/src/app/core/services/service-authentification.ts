import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  DonneesInscription,
  IdentifiantsConnexion,
  ReponseAuthentification,
  ReponseRafraichissement,
} from '../models/authentification.model';
import { Journaliste } from '../models/journaliste.model';
import { ServiceJetons } from './service-jetons';

@Injectable({ providedIn: 'root' })
export class ServiceAuthentification {
  private readonly http = inject(HttpClient);
  private readonly jetons = inject(ServiceJetons);
  private readonly urlBase = `${environment.apiUrl}authentification`;

  readonly profil = signal<Journaliste | null>(null);
  readonly estConnecte = computed(
    () => this.profil() !== null || this.jetons.aUnJetonAcces(),
  );

  connexion(donnees: IdentifiantsConnexion): Observable<ReponseAuthentification> {
    return this.http
      .post<ReponseAuthentification>(`${this.urlBase}/connexion/`, donnees)
      .pipe(
        tap((reponse) => {
          this.jetons.enregistrerJetons(
            reponse.jeton_acces,
            reponse.jeton_rafraichissement,
          );
          this.profil.set(reponse.journaliste);
        }),
      );
  }

  inscription(donnees: DonneesInscription): Observable<ReponseAuthentification> {
    return this.http
      .post<ReponseAuthentification>(`${this.urlBase}/inscription/`, donnees)
      .pipe(
        tap((reponse) => {
          this.jetons.enregistrerJetons(
            reponse.jeton_acces,
            reponse.jeton_rafraichissement,
          );
          this.profil.set(reponse.journaliste);
        }),
      );
  }

  rafraichirJeton(): Observable<ReponseRafraichissement> {
    const jetonRafraichissement = this.jetons.obtenirJetonRafraichissement();
    return this.http
      .post<ReponseRafraichissement>(`${this.urlBase}/rafraichir-token/`, {
        jeton_rafraichissement: jetonRafraichissement,
      })
      .pipe(
        tap((reponse) => {
          this.jetons.enregistrerJetonAcces(reponse.jeton_acces);
        }),
      );
  }

  obtenirProfil(): Observable<Journaliste> {
    return this.http
      .get<Journaliste>(`${this.urlBase}/profil/`)
      .pipe(tap((profil) => this.profil.set(profil)));
  }

  initialiserProfil(): void {
    if (!this.jetons.aUnJetonAcces() || this.profil() !== null) {
      return;
    }
    this.obtenirProfil().subscribe({
      error: () => {
        this.deconnexion();
      },
    });
  }

  deconnexion(): void {
    this.jetons.supprimerJetons();
    this.profil.set(null);
  }
}
