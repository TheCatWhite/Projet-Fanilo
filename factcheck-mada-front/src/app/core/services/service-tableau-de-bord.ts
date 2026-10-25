import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { StatistiquesTableauDeBord } from '../models/tableau-de-bord.model';

@Injectable({ providedIn: 'root' })
export class ServiceTableauDeBord {
  private readonly http = inject(HttpClient);

  obtenirStatistiques(): Observable<StatistiquesTableauDeBord> {
    return this.http.get<StatistiquesTableauDeBord>(
      `${environment.apiUrl}tableau-de-bord/statistiques/`,
    );
  }
}
