import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { intercepteurJwt } from './intercepteur-jwt';

describe('intercepteurJwt', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([intercepteurJwt])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('ajoute le JWT aux requêtes privées', () => {
    localStorage.setItem('factcheck.jeton_acces', 'jeton-acces');

    http.get('/api/rumeurs/').subscribe();
    const requete = httpMock.expectOne('/api/rumeurs/');

    expect(requete.request.headers.get('Authorization')).toBe('Bearer jeton-acces');
    requete.flush([]);
  });

  it('rafraîchit le jeton après un 401 puis rejoue la requête', () => {
    localStorage.setItem('factcheck.jeton_acces', 'jeton-expire');
    localStorage.setItem('factcheck.jeton_rafraichissement', 'jeton-rafraichissement');

    http.get('/api/rumeurs/').subscribe();

    const premiere = httpMock.expectOne('/api/rumeurs/');
    expect(premiere.request.headers.get('Authorization')).toBe('Bearer jeton-expire');
    premiere.flush({ detail: 'Jeton expiré.' }, { status: 401, statusText: 'Unauthorized' });

    const rafraichissement = httpMock.expectOne(
      'http://localhost:8000/api/authentification/rafraichir-token/',
    );
    expect(rafraichissement.request.method).toBe('POST');
    rafraichissement.flush({
      jeton_acces: 'jeton-renouvele',
      message: 'Jeton d’accès renouvelé.',
    });

    const rejoue = httpMock.expectOne('/api/rumeurs/');
    expect(rejoue.request.headers.get('Authorization')).toBe('Bearer jeton-renouvele');
    rejoue.flush([]);

    expect(localStorage.getItem('factcheck.jeton_acces')).toBe('jeton-renouvele');
  });

  it('ne déconnecte pas si la requête rejouée échoue après le refresh', () => {
    localStorage.setItem('factcheck.jeton_acces', 'jeton-expire');
    localStorage.setItem('factcheck.jeton_rafraichissement', 'jeton-rafraichissement');

    http.get('/api/rumeurs/').subscribe({ error: () => undefined });

    const premiere = httpMock.expectOne('/api/rumeurs/');
    premiere.flush({ detail: 'Jeton expiré.' }, { status: 401, statusText: 'Unauthorized' });

    const rafraichissement = httpMock.expectOne(
      'http://localhost:8000/api/authentification/rafraichir-token/',
    );
    rafraichissement.flush({
      jeton_acces: 'jeton-renouvele',
      message: 'Jeton d’accès renouvelé.',
    });

    const rejoue = httpMock.expectOne('/api/rumeurs/');
    rejoue.flush(
      { detail: 'Erreur serveur.' },
      { status: 500, statusText: 'Internal Server Error' },
    );

    expect(localStorage.getItem('factcheck.jeton_acces')).toBe('jeton-renouvele');
    expect(localStorage.getItem('factcheck.jeton_rafraichissement')).toBe('jeton-rafraichissement');
  });
});
