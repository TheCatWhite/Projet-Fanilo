import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AnalyseTexte } from '../models/analyse.model';
import { ArbrePropagation } from '../models/arbre-propagation.model';

@Injectable({ providedIn: 'root' })
export class ServiceAnalyse {
  private readonly http = inject(HttpClient);
  private readonly urlRumeurs = `${environment.apiUrl}rumeurs`;

  analyserTexte(rumeurId: number): Observable<AnalyseTexte> {
    return this.http.post<AnalyseTexte>(`${this.urlRumeurs}/${rumeurId}/analyser-texte/`, {});
  }

  obtenirArbrePropagation(rumeurId: number): Observable<ArbrePropagation> {
    return this.http.get<ArbrePropagation>(`${this.urlRumeurs}/${rumeurId}/arbre-propagation/`);
  }
}
