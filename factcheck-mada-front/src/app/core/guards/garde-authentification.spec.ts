import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  Router,
  RouterStateSnapshot,
  UrlTree,
  provideRouter,
} from '@angular/router';

import { gardeAuthentification } from './garde-authentification';
import { ServiceJetons } from '../services/service-jetons';

describe('gardeAuthentification', () => {
  const etat = { url: '/rumeurs' } as RouterStateSnapshot;
  const route = {} as ActivatedRouteSnapshot;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideRouter([])],
    });
  });

  afterEach(() => localStorage.clear());

  it('redirige vers la connexion sans jeton', () => {
    const resultat = TestBed.runInInjectionContext(() => gardeAuthentification(route, etat));

    expect(resultat).toBeInstanceOf(UrlTree);
    expect(String(resultat)).toContain('/connexion');
    expect(String(resultat)).toContain('retour');
  });

  it('autorise l’accès avec un jeton d’accès', () => {
    localStorage.setItem('factcheck.jeton_acces', 'jeton-test');
    TestBed.inject(ServiceJetons);
    expect(TestBed.inject(Router)).toBeTruthy();

    const resultat = TestBed.runInInjectionContext(() => gardeAuthentification(route, etat));

    expect(resultat).toBe(true);
  });
});
