import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin, of, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { ArbrePropagation } from '../../../core/models/arbre-propagation.model';
import {
  NiveauRisque,
  RapportVerification,
} from '../../../core/models/rapport-verification.model';
import { RumeurDetail } from '../../../core/models/rumeur.model';
import { ServiceAnalyse } from '../../../core/services/service-analyse';
import { ServiceErreur } from '../../../core/services/service-erreur';
import { ServiceRapport } from '../../../core/services/service-rapport';
import { ServiceRumeur } from '../../../core/services/service-rumeur';
import { ComposantBadgeRisque } from '../../../shared/composants/badge-risque/badge-risque.component';
import { ComposantBadgeSourceZero } from '../../../shared/composants/badge-source-zero/badge-source-zero.component';
import { ComposantCarteAlerte } from '../../../shared/composants/carte-alerte/carte-alerte.component';
import { ComposantCartePublication } from '../../../shared/composants/carte-publication/carte-publication.component';
import { ComposantChargeur } from '../../../shared/composants/chargeur/chargeur.component';
import { ComposantEtatVide } from '../../../shared/composants/etat-vide/etat-vide.component';
import { ComposantMessageErreur } from '../../../shared/composants/message-erreur/message-erreur.component';
import { PipeDateFrancaise } from '../../../shared/pipes/pipe-date-francaise';
import { telechargerBlob } from '../../../shared/utilitaires/telecharger-fichier';

@Component({
  selector: 'app-fiche-verification',
  standalone: true,
  imports: [
    RouterLink,
    ComposantBadgeRisque,
    ComposantBadgeSourceZero,
    ComposantCarteAlerte,
    ComposantCartePublication,
    ComposantChargeur,
    ComposantEtatVide,
    ComposantMessageErreur,
    PipeDateFrancaise,
  ],
  templateUrl: './fiche-verification.component.html',
  styleUrl: './fiche-verification.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantFicheVerification {
  private readonly route = inject(ActivatedRoute);
  private readonly serviceRumeur = inject(ServiceRumeur);
  private readonly serviceAnalyse = inject(ServiceAnalyse);
  private readonly serviceRapport = inject(ServiceRapport);
  private readonly serviceErreur = inject(ServiceErreur);

  readonly rumeurId = Number(this.route.snapshot.paramMap.get('id'));
  readonly chargement = signal(true);
  readonly generation = signal(false);
  readonly telechargementPdf = signal(false);
  readonly telechargementImage = signal(false);
  readonly messagesErreur = signal<string[]>([]);
  readonly messagesSucces = signal<string[]>([]);
  readonly rumeur = signal<RumeurDetail | null>(null);
  readonly arbre = signal<ArbrePropagation | null>(null);
  readonly rapport = signal<RapportVerification | null>(null);

  readonly premierePublication = computed(
    () =>
      this.rumeur()?.publications.find(
        (publication) => publication.est_premiere_detection,
      ) ?? null,
  );

  readonly noeudsTries = computed(() =>
    [...(this.arbre()?.noeuds ?? [])].sort(
      (a, b) =>
        new Date(a.date_publication).getTime() -
        new Date(b.date_publication).getTime(),
    ),
  );

  constructor() {
    if (!Number.isInteger(this.rumeurId) || this.rumeurId <= 0) {
      this.chargement.set(false);
      this.messagesErreur.set(['Identifiant de rumeur invalide.']);
      return;
    }
    this.charger();
  }

  charger(): void {
    this.chargement.set(true);
    this.messagesErreur.set([]);
    this.messagesSucces.set([]);

    forkJoin({
      rumeur: this.serviceRumeur.obtenirRumeur(this.rumeurId),
      arbre: this.serviceAnalyse.obtenirArbrePropagation(this.rumeurId),
      rapport: this.serviceRapport.obtenirRapport(this.rumeurId).pipe(
        catchError((erreur: unknown) => {
          if (erreur instanceof HttpErrorResponse && erreur.status === 404) {
            return of(null);
          }
          return throwError(() => erreur);
        }),
      ),
    }).subscribe({
      next: ({ rumeur, arbre, rapport }) => {
        this.rumeur.set(rumeur);
        this.arbre.set(arbre);
        this.rapport.set(rapport);
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargement.set(false);
      },
      complete: () => this.chargement.set(false),
    });
  }

  genererRapport(): void {
    if (this.generation()) {
      return;
    }

    this.generation.set(true);
    this.messagesErreur.set([]);
    this.messagesSucces.set([]);

    this.serviceRapport.genererRapport(this.rumeurId).subscribe({
      next: (reponse) => {
        this.rapport.set(reponse.rapport);
        this.messagesSucces.set([reponse.message]);
        this.rafraichirContexte();
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.generation.set(false);
      },
      complete: () => this.generation.set(false),
    });
  }

  telechargerPdf(): void {
    if (!this.rapport() || this.telechargementPdf()) {
      return;
    }

    this.telechargementPdf.set(true);
    this.messagesErreur.set([]);
    this.serviceRapport.telechargerPdf(this.rumeurId).subscribe({
      next: (blob) => {
        telechargerBlob(blob, `rapport-verification-${this.rumeurId}.pdf`);
        this.messagesSucces.set(['Le rapport PDF a été téléchargé.']);
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.telechargementPdf.set(false);
      },
      complete: () => this.telechargementPdf.set(false),
    });
  }

  telechargerImage(): void {
    if (!this.rapport() || this.telechargementImage()) {
      return;
    }

    this.telechargementImage.set(true);
    this.messagesErreur.set([]);
    this.serviceRapport.telechargerImage(this.rumeurId).subscribe({
      next: (blob) => {
        telechargerBlob(blob, `rapport-verification-${this.rumeurId}.png`);
        this.messagesSucces.set(['L’image du rapport a été téléchargée.']);
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.telechargementImage.set(false);
      },
      complete: () => this.telechargementImage.set(false),
    });
  }

  jauge(): string {
    const score = Math.max(0, Math.min(100, this.rapport()?.score_credibilite ?? 0));
    return `conic-gradient(${this.couleurRisque()} ${score}%, #e7edf2 ${score}% 100%)`;
  }

  private couleurRisque(): string {
    switch (this.rapport()?.niveau_risque) {
      case 'faible':
        return '#2f7d5b';
      case 'moyen':
        return '#d89a25';
      case 'eleve':
        return '#c65353';
      case 'tres_eleve':
        return '#7d1d1d';
      default:
        return '#1f5f8b';
    }
  }

  private rafraichirContexte(): void {
    forkJoin({
      rumeur: this.serviceRumeur.obtenirRumeur(this.rumeurId),
      arbre: this.serviceAnalyse.obtenirArbrePropagation(this.rumeurId),
    }).subscribe({
      next: ({ rumeur, arbre }) => {
        this.rumeur.set(rumeur);
        this.arbre.set(arbre);
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
      },
    });
  }

  niveauRisqueLibelle(niveau: NiveauRisque | null): string {
    switch (niveau) {
      case 'faible':
        return 'Risque faible';
      case 'moyen':
        return 'Risque moyen';
      case 'eleve':
        return 'Risque élevé';
      case 'tres_eleve':
        return 'Risque très élevé';
      default:
        return 'Non évalué';
    }
  }
}
