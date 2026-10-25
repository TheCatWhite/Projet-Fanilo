import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { ServiceJetons } from '../services/service-jetons';

/**
 * Protège les écrans privés. Le jeton peut être expiré : l'intercepteur
 * tentera alors un rafraîchissement avant de renvoyer l'utilisateur ici.
 */
export const gardeAuthentification: CanActivateFn = (_route, etat) => {
  const jetons = inject(ServiceJetons);
  const routeur = inject(Router);

  if (jetons.aUnJetonAcces()) {
    return true;
  }

  return routeur.createUrlTree(['/connexion'], {
    queryParams: { retour: etat.url },
  });
};
