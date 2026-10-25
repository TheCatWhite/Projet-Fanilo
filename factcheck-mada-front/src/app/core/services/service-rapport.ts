import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { RapportVerification, ReponseRapportGenere } from '../models/rapport-verification.model';

@Injectable({ providedIn: 'root' })
export class ServiceRapport {
  private readonly http = inject(HttpClient);
  private readonly urlRumeurs = `${environment.apiUrl}rumeurs`;

  genererRapport(rumeurId: number): Observable<ReponseRapportGenere> {
    return this.http.post<ReponseRapportGenere>(
      `${this.urlRumeurs}/${rumeurId}/generer-rapport/`,
      {},
    );
  }

  obtenirRapport(rumeurId: number): Observable<RapportVerification> {
    return this.http.get<RapportVerification>(`${this.urlRumeurs}/${rumeurId}/rapport/`);
  }

  telechargerPdf(rumeurId: number): Observable<Blob> {
    return this.http.get(`${this.urlRumeurs}/${rumeurId}/rapport/pdf/`, { responseType: 'blob' });
  }

  telechargerImage(rumeurId: number): Observable<Blob> {
    return this.http.get(`${this.urlRumeurs}/${rumeurId}/rapport/image/`, { responseType: 'blob' });
  }
}
