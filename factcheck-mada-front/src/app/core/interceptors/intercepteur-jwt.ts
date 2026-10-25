import {
  HttpBackend,
  HttpErrorResponse,
  HttpEvent,
  HttpHeaders,
  HttpInterceptorFn,
  HttpRequest,
  HttpResponse,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  Observable,
  catchError,
  filter,
  finalize,
  map,
  shareReplay,
  switchMap,
  throwError,
} from 'rxjs';

import { environment } from '../../../environments/environment';
import { ReponseRafraichissement } from '../models/authentification.model';
import { ServiceJetons } from '../services/service-jetons';

const CHEMINS_PUBLICS = [
  '/authentification/inscription/',
  '/authentification/connexion/',
  '/authentification/rafraichir-token/',
];

let rafraichissementEnCours$: Observable<string> | null = null;

/**
 * Ajoute le JWT, tente un rafraîchissement unique sur 401, puis rejoue la
 * requête initiale. Le rafraîchissement utilise HttpBackend pour ne pas être
 * intercepté par lui-même.
 */
export const intercepteurJwt: HttpInterceptorFn = (requete, suivant) => {
  const jetons = inject(ServiceJetons);
  const routeur = inject(Router);
  const backend = inject(HttpBackend);
  const publique = CHEMINS_PUBLICS.some((chemin) => requete.url.includes(chemin));
  const jetonAcces = jetons.obtenirJetonAcces();
  const requeteAutorisee =
    jetonAcces && !publique
      ? requete.clone({
          setHeaders: { Authorization: `Bearer ${jetonAcces}` },
        })
      : requete;

  return suivant(requeteAutorisee).pipe(
    catchError((erreur: unknown) => {
      if (
        publique ||
        !(erreur instanceof HttpErrorResponse) ||
        erreur.status !== 401
      ) {
        return throwError(() => erreur);
      }

      const jetonRafraichissement = jetons.obtenirJetonRafraichissement();
      if (!jetonRafraichissement) {
        deconnecter(routeur, jetons);
        return throwError(() => erreur);
      }

      return rafraichir(backend, jetons, jetonRafraichissement).pipe(
        switchMap((nouveauJeton) =>
          suivant(
            requete.clone({
              setHeaders: { Authorization: `Bearer ${nouveauJeton}` },
            }),
          ),
        ),
        catchError((erreurRafraichissement: unknown) => {
          deconnecter(routeur, jetons);
          return throwError(() => erreurRafraichissement);
        }),
      );
    }),
  );
};

function rafraichir(
  backend: HttpBackend,
  jetons: ServiceJetons,
  jetonRafraichissement: string,
): Observable<string> {
  if (rafraichissementEnCours$) {
    return rafraichissementEnCours$;
  }

  const url = `${environment.apiUrl}authentification/rafraichir-token/`;
  const corps = JSON.stringify({
    jeton_rafraichissement: jetonRafraichissement,
  });
  const requete = new HttpRequest('POST', url, corps, {
    headers: new HttpHeaders({ 'Content-Type': 'application/json' }),
  });

  rafraichissementEnCours$ = backend.handle(requete).pipe(
    filter(
      (evenement): evenement is HttpResponse<ReponseRafraichissement> =>
        evenement instanceof HttpResponse,
    ),
    map((reponse) => {
      const nouveauJeton = reponse.body?.jeton_acces;
      if (!nouveauJeton) {
        throw new Error('Le serveur n’a pas renvoyé de nouveau jeton d’accès.');
      }
      jetons.enregistrerJetonAcces(nouveauJeton);
      return nouveauJeton;
    }),
    finalize(() => {
      rafraichissementEnCours$ = null;
    }),
    shareReplay({ bufferSize: 1, refCount: false }),
  );

  return rafraichissementEnCours$;
}

function deconnecter(routeur: Router, jetons: ServiceJetons): void {
  jetons.supprimerJetons();
  if (routeur.url !== '/connexion') {
    void routeur.navigate(['/connexion'], {
      queryParams: { retour: routeur.url },
    });
  }
}
