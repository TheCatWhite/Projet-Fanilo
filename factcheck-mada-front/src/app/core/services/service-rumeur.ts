import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AnalyseTexte } from '../models/analyse.model';
import { ReponsePaginee } from '../models/reponse-paginee.model';
import {
  DonneesCreationRumeur,
  DonneesModificationRumeur,
  FiltresRumeurs,
  ReponseCreationRumeur,
  RumeurDetail,
  RumeurListe,
} from '../models/rumeur.model';
import { ServiceAnalyse } from './service-analyse';

@Injectable({ providedIn: 'root' })
export class ServiceRumeur {
  private readonly http = inject(HttpClient);
  private readonly serviceAnalyse = inject(ServiceAnalyse);
  private readonly urlRumeurs = `${environment.apiUrl}rumeurs`;

  obtenirRumeurs(filtres: FiltresRumeurs = {}): Observable<ReponsePaginee<RumeurListe>> {
    let parametres = new HttpParams();

    if (filtres.page !== undefined) {
      parametres = parametres.set('page', String(filtres.page));
    }
    if (filtres.taille_page !== undefined) {
      parametres = parametres.set('taille_page', String(filtres.taille_page));
    }
    if (filtres.statut) {
      parametres = parametres.set('statut', filtres.statut);
    }
    if (filtres.titre?.trim()) {
      parametres = parametres.set('titre', filtres.titre.trim());
    }
    if (filtres.recherche?.trim()) {
      parametres = parametres.set('recherche', filtres.recherche.trim());
    }
    if (filtres.date_debut) {
      parametres = parametres.set('date_debut', filtres.date_debut);
    }
    if (filtres.date_fin) {
      parametres = parametres.set('date_fin', filtres.date_fin);
    }
    if (filtres.tri) {
      parametres = parametres.set('tri', filtres.tri);
    }

    return this.http.get<ReponsePaginee<RumeurListe>>(`${this.urlRumeurs}/`, {
      params: parametres,
    });
  }

  creerRumeur(donnees: DonneesCreationRumeur): Observable<ReponseCreationRumeur> {
    return this.http.post<ReponseCreationRumeur>(`${this.urlRumeurs}/`, donnees);
  }

  obtenirRumeur(id: number): Observable<RumeurDetail> {
    return this.http.get<RumeurDetail>(`${this.urlRumeurs}/${id}/`);
  }

  modifierRumeur(id: number, donnees: DonneesModificationRumeur): Observable<RumeurDetail> {
    return this.http.patch<RumeurDetail>(`${this.urlRumeurs}/${id}/`, donnees);
  }

  supprimerRumeur(id: number): Observable<void> {
    return this.http.delete<void>(`${this.urlRumeurs}/${id}/`);
  }

  /**
   * L'analyse de texte est portée par le service d'analyse ; cette méthode
   * conserve l'API demandée par l'écran de détail.
   */
  analyserTexte(id: number): Observable<AnalyseTexte> {
    return this.serviceAnalyse.analyserTexte(id);
  }
}
