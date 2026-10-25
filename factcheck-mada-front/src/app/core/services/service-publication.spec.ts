import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { PublicationSource } from '../models/publication-source.model';
import { ServicePublication } from './service-publication';

describe('ServicePublication', () => {
  let service: ServicePublication;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ServicePublication, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ServicePublication);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('construit un FormData avec les métadonnées et la capture', () => {
    const capture = new File(['contenu-image'], 'capture.png', {
      type: 'image/png',
    });

    service
      .ajouterPublication(7, {
        plateforme: 'facebook',
        nom_auteur: 'Mada Info',
        url_publication: 'https://example.mg/publication',
        date_publication: '2026-10-25T10:00:00.000Z',
        nombre_abonnes: 12000,
        texte_brut: 'Texte de la publication',
        capture_ecran: capture,
      })
      .subscribe((reponse) => {
        expect(reponse.publication.id).toBe(12);
      });

    const requete = http.expectOne('http://localhost:8000/api/rumeurs/7/publications/');
    expect(requete.request.method).toBe('POST');

    const corps = requete.request.body as FormData;
    expect(corps).toBeInstanceOf(FormData);
    expect(corps.get('plateforme')).toBe('facebook');
    expect(corps.get('nom_auteur')).toBe('Mada Info');
    expect(corps.get('nombre_abonnes')).toBe('12000');
    expect(corps.get('capture_ecran')).toBeInstanceOf(File);

    requete.flush({
      message: 'Publication enregistrée.',
      publication: { id: 12 } as PublicationSource,
      liens_crees: [],
      alertes_compte: [],
      analyse_texte: {
        score_risque_texte: 0,
        nombre_alertes: 0,
        alertes: [],
      },
      premiere_publication_detectee: null,
    });
  });

  it('appelle l’analyse de compte avec le JWT du service', () => {
    service.analyserCompte(12).subscribe((analyse) => {
      expect(analyse.publication_id).toBe(12);
    });

    const requete = http.expectOne('http://localhost:8000/api/publications/12/analyser-compte/');
    expect(requete.request.method).toBe('POST');
    requete.flush({
      publication_id: 12,
      nombre_alertes: 0,
      alertes: [],
      message: 'Analyse terminée.',
    });
  });
});
