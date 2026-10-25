import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AnalyseCompte } from '../models/analyse.model';
import {
  DonneesPublication,
  PublicationSource,
  ReponseCreationPublication,
} from '../models/publication-source.model';

@Injectable({ providedIn: 'root' })
export class ServicePublication {
  private readonly http = inject(HttpClient);
  private readonly urlRumeurs = `${environment.apiUrl}rumeurs`;
  private readonly urlPublications = `${environment.apiUrl}publications`;

  obtenirPublications(rumeurId: number): Observable<PublicationSource[]> {
    return this.http.get<PublicationSource[]>(`${this.urlRumeurs}/${rumeurId}/publications/`);
  }

  ajouterPublication(
    rumeurId: number,
    donnees: DonneesPublication,
  ): Observable<ReponseCreationPublication> {
    return this.http.post<ReponseCreationPublication>(
      `${this.urlRumeurs}/${rumeurId}/publications/`,
      this.construireFormData(donnees),
    );
  }

  analyserCompte(publicationId: number): Observable<AnalyseCompte> {
    return this.http.post<AnalyseCompte>(
      `${this.urlPublications}/${publicationId}/analyser-compte/`,
      {},
    );
  }

  private construireFormData(donnees: DonneesPublication): FormData {
    const formulaire = new FormData();
    formulaire.append('plateforme', donnees.plateforme);
    formulaire.append('nom_auteur', donnees.nom_auteur);
    formulaire.append('date_publication', donnees.date_publication);

    if (donnees.url_publication?.trim()) {
      formulaire.append('url_publication', donnees.url_publication.trim());
    }
    if (donnees.url_profil_auteur?.trim()) {
      formulaire.append('url_profil_auteur', donnees.url_profil_auteur.trim());
    }
    if (donnees.date_creation_compte) {
      formulaire.append('date_creation_compte', donnees.date_creation_compte);
    }
    if (donnees.nombre_abonnes !== undefined && donnees.nombre_abonnes !== null) {
      formulaire.append('nombre_abonnes', String(donnees.nombre_abonnes));
    }
    if (donnees.texte_brut?.trim()) {
      formulaire.append('texte_brut', donnees.texte_brut.trim());
    }
    if (donnees.capture_ecran) {
      formulaire.append('capture_ecran', donnees.capture_ecran, donnees.capture_ecran.name);
    }

    return formulaire;
  }
}
