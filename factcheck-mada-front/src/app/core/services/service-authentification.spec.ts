import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { Journaliste } from '../models/journaliste.model';
import { ServiceAuthentification } from './service-authentification';

const PROFIL: Journaliste = {
  id: 1,
  nom_utilisateur: 'demo',
  email: 'demo@example.mg',
  redaction: 'Rédaction test',
  role: 'journaliste',
  date_inscription: '2026-10-25T10:00:00Z',
  est_administrateur: false,
};

describe('ServiceAuthentification', () => {
  let service: ServiceAuthentification;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [ServiceAuthentification, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ServiceAuthentification);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  it('enregistre les jetons et le profil après connexion', () => {
    service
      .connexion({ nom_utilisateur: 'demo', mot_de_passe: 'Demo1234!' })
      .subscribe((reponse) => {
        expect(reponse.journaliste.nom_utilisateur).toBe('demo');
      });

    const requete = http.expectOne('http://localhost:8000/api/authentification/connexion/');
    expect(requete.request.method).toBe('POST');
    expect(requete.request.body).toEqual({
      nom_utilisateur: 'demo',
      mot_de_passe: 'Demo1234!',
    });

    requete.flush({
      message: 'Connexion réussie.',
      journaliste: PROFIL,
      jeton_acces: 'jeton-acces-test',
      jeton_rafraichissement: 'jeton-rafraichissement-test',
    });

    expect(localStorage.getItem('factcheck.jeton_acces')).toBe('jeton-acces-test');
    expect(localStorage.getItem('factcheck.jeton_rafraichissement')).toBe(
      'jeton-rafraichissement-test',
    );
    expect(service.profil()).toEqual(PROFIL);
  });

  it('supprime les jetons et le profil à la déconnexion', () => {
    localStorage.setItem('factcheck.jeton_acces', 'acces');
    localStorage.setItem('factcheck.jeton_rafraichissement', 'rafraichissement');
    service.profil.set(PROFIL);

    service.deconnexion();

    expect(localStorage.getItem('factcheck.jeton_acces')).toBeNull();
    expect(localStorage.getItem('factcheck.jeton_rafraichissement')).toBeNull();
    expect(service.profil()).toBeNull();
  });

  it('rafraîchit uniquement le jeton d’accès', () => {
    localStorage.setItem('factcheck.jeton_rafraichissement', 'ancien-rafraichissement');

    service.rafraichirJeton().subscribe((reponse) => {
      expect(reponse.jeton_acces).toBe('nouveau-jeton');
    });

    const requete = http.expectOne('http://localhost:8000/api/authentification/rafraichir-token/');
    expect(requete.request.method).toBe('POST');
    expect(requete.request.body).toEqual({
      jeton_rafraichissement: 'ancien-rafraichissement',
    });
    requete.flush({
      jeton_acces: 'nouveau-jeton',
      message: 'Jeton d’accès renouvelé.',
    });

    expect(localStorage.getItem('factcheck.jeton_acces')).toBe('nouveau-jeton');
  });
});
