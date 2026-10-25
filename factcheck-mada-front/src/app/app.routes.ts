import { Routes } from '@angular/router';

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
  { path: '', pathMatch: 'full', redirectTo: 'connexion' },
  { path: '**', redirectTo: 'connexion' },
];
