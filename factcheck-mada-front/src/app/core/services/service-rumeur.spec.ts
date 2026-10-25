import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { RumeurDetail } from '../models/rumeur.model';
import { ServiceRumeur } from './service-rumeur';

describe('ServiceRumeur', () => {
  let service: ServiceRumeur;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ServiceRumeur, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ServiceRumeur);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('transmet les filtres de recherche et de pagination à Django', () => {
    service
      .obtenirRumeurs({
        page: 2,
        taille_page: 10,
        recherche: 'carburant',
        statut: 'en_analyse',
      })
      .subscribe((reponse) => {
        expect(reponse.total).toBe(0);
        expect(reponse.resultats).toEqual([]);
      });

    const requete = http.expectOne(
      (demande) => demande.url === 'http://localhost:8000/api/rumeurs/' && demande.method === 'GET',
    );
    expect(requete.request.params.get('page')).toBe('2');
    expect(requete.request.params.get('taille_page')).toBe('10');
    expect(requete.request.params.get('recherche')).toBe('carburant');
    expect(requete.request.params.get('statut')).toBe('en_analyse');

    requete.flush({
      total: 0,
      suivant: null,
      precedent: null,
      resultats: [],
    });
  });

  it('crée une rumeur et conserve le drapeau de doublon', () => {
    service
      .creerRumeur({
        titre: 'Une rumeur de test',
        contenu: 'Contenu sufficient pour le test de création.',
        langue: 'fr',
      })
      .subscribe((reponse) => {
        expect(reponse.cree).toBe(false);
        expect(reponse.message).toContain('déjà');
      });

    const requete = http.expectOne('http://localhost:8000/api/rumeurs/');
    expect(requete.request.method).toBe('POST');
    requete.flush({
      cree: false,
      message: 'Une rumeur identique existe déjà.',
      rumeur: { id: 7 } as RumeurDetail,
      similaires: [],
    });
  });

  it('appelle l’endpoint d’analyse textuelle', () => {
    service.analyserTexte(7).subscribe((analyse) => {
      expect(analyse.nombre_alertes).toBe(0);
    });

    const requete = http.expectOne('http://localhost:8000/api/rumeurs/7/analyser-texte/');
    expect(requete.request.method).toBe('POST');
    requete.flush({
      rumeur_id: 7,
      score_risque_texte: 0,
      nombre_alertes: 0,
      alertes: [],
    });
  });
});
