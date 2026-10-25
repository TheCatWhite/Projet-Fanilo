import { Routes } from '@angular/router';

import { gardeAuthentification } from './core/guards/garde-authentification';

export const routes: Routes = [
  {
    path: 'connexion',
    title: 'Connexion | FactCheck Mada',
    loadComponent: () =>
      import('./features/authentification/connexion/connexion.component').then(
        (module) => module.ComposantConnexion,
      ),
  },
  {
    path: 'inscription',
    title: 'Inscription | FactCheck Mada',
    loadComponent: () =>
      import('./features/authentification/inscription/inscription.component').then(
        (module) => module.ComposantInscription,
      ),
  },
  {
    path: 'tableau-de-bord',
    title: 'Tableau de bord | FactCheck Mada',
    canActivate: [gardeAuthentification],
    loadComponent: () =>
      import(
        './features/tableau-de-bord/tableau-de-bord/tableau-de-bord.component'
      ).then((module) => module.ComposantTableauDeBord),
  },
  {
    path: 'rumeurs',
    title: 'Rumeurs | FactCheck Mada',
    canActivate: [gardeAuthentification],
    loadComponent: () =>
      import('./features/rumeurs/liste-rumeurs/liste-rumeurs.component').then(
        (module) => module.ComposantListeRumeurs,
      ),
  },
  {
    path: 'rumeurs/nouvelle',
    title: 'Nouvelle rumeur | FactCheck Mada',
    canActivate: [gardeAuthentification],
    loadComponent: () =>
      import('./features/rumeurs/creer-rumeur/creer-rumeur.component').then(
        (module) => module.ComposantCreerRumeur,
      ),
  },
  {
    path: 'rumeurs/:id/publications/ajouter',
    title: 'Ajouter une publication | FactCheck Mada',
    canActivate: [gardeAuthentification],
    loadComponent: () =>
      import(
        './features/publications/ajouter-publication/ajouter-publication.component'
      ).then((module) => module.ComposantAjouterPublication),
  },
  {
    path: 'rumeurs/:id/propagation',
    title: 'Propagation | FactCheck Mada',
    canActivate: [gardeAuthentification],
    loadComponent: () =>
      import(
        './features/propagation/arbre-propagation/arbre-propagation.component'
      ).then((module) => module.ComposantArbrePropagation),
  },
  {
    path: 'rumeurs/:id',
    title: 'Dossier de rumeur | FactCheck Mada',
    canActivate: [gardeAuthentification],
    loadComponent: () =>
      import('./features/rumeurs/detail-rumeur/detail-rumeur.component').then(
        (module) => module.ComposantDetailRumeur,
      ),
  },
  { path: '', pathMatch: 'full', redirectTo: 'tableau-de-bord' },
  { path: '**', redirectTo: 'tableau-de-bord' },
];
