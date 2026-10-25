import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { distinctUntilChanged, map } from 'rxjs';

import { RumeurDetail } from '../../../core/models/rumeur.model';
import { ServiceErreur } from '../../../core/services/service-erreur';
import { ServiceRumeur } from '../../../core/services/service-rumeur';
import { ComposantBadgeRisque } from '../../../shared/composants/badge-risque/badge-risque.component';
import { ComposantCarteAlerte } from '../../../shared/composants/carte-alerte/carte-alerte.component';
import { ComposantCartePublication } from '../../../shared/composants/carte-publication/carte-publication.component';
import { ComposantChargeur } from '../../../shared/composants/chargeur/chargeur.component';
import { ComposantEtatVide } from '../../../shared/composants/etat-vide/etat-vide.component';
import { ComposantMessageErreur } from '../../../shared/composants/message-erreur/message-erreur.component';
import { PipeDateFrancaise } from '../../../shared/pipes/pipe-date-francaise';

@Component({
  selector: 'app-detail-rumeur',
  standalone: true,
  imports: [
    RouterLink,
    ComposantBadgeRisque,
    ComposantCarteAlerte,
    ComposantCartePublication,
    ComposantChargeur,
    ComposantEtatVide,
    ComposantMessageErreur,
    PipeDateFrancaise,
  ],
  templateUrl: './detail-rumeur.component.html',
  styleUrl: './detail-rumeur.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantDetailRumeur {
  private readonly route = inject(ActivatedRoute);
  private readonly routeur = inject(Router);
  private readonly serviceRumeur = inject(ServiceRumeur);
  private readonly serviceErreur = inject(ServiceErreur);
  private readonly destroyRef = inject(DestroyRef);

  readonly chargement = signal(true);
  readonly chargementAnalyse = signal(false);
  readonly chargementSuppression = signal(false);
  readonly messagesErreur = signal<string[]>([]);
  readonly messagesSucces = signal<string[]>([]);
  readonly rumeur = signal<RumeurDetail | null>(null);
  readonly rumeurId = signal<number | null>(null);

  readonly premierePublication = computed(
    () =>
      this.rumeur()?.publications.find(
        (publication) => publication.est_premiere_detection,
      ) ?? null,
  );

  readonly publicationsTriees = computed(() =>
    [...(this.rumeur()?.publications ?? [])].sort(
      (a, b) =>
        new Date(a.date_publication).getTime() -
        new Date(b.date_publication).getTime(),
    ),
  );

  constructor() {
    this.route.paramMap
      .pipe(
        map((parametres) => Number(parametres.get('id'))),
        distinctUntilChanged(),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((id) => {
        if (!Number.isInteger(id) || id <= 0) {
          this.chargement.set(false);
          this.messagesErreur.set(['Identifiant de rumeur invalide.']);
          return;
        }
        this.charger(id);
      });
  }

  charger(id: number, afficherChargeur = true): void {
    this.rumeurId.set(id);
    if (afficherChargeur) {
      this.chargement.set(true);
    }
    this.messagesErreur.set([]);

    this.serviceRumeur.obtenirRumeur(id).subscribe({
      next: (rumeur) => {
        this.rumeur.set(rumeur);
        this.lireMessageRetour();
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargement.set(false);
      },
      complete: () => this.chargement.set(false),
    });
  }

  analyserTexte(): void {
    const id = this.rumeurId();
    if (!id || this.chargementAnalyse()) {
      return;
    }

    this.chargementAnalyse.set(true);
    this.messagesErreur.set([]);
    this.messagesSucces.set([]);

    this.serviceRumeur.analyserTexte(id).subscribe({
      next: (analyse) => {
        this.messagesSucces.set([
          `Analyse textuelle terminée : ${analyse.nombre_alertes} alerte(s), score de risque ${analyse.score_risque_texte}/100.`,
        ]);
        this.charger(id, false);
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargementAnalyse.set(false);
      },
      complete: () => this.chargementAnalyse.set(false),
    });
  }

  supprimer(): void {
    const id = this.rumeurId();
    const rumeur = this.rumeur();
    if (!id || !rumeur || this.chargementSuppression()) {
      return;
    }

    const confirmation = window.confirm(
      `Supprimer définitivement la rumeur « ${rumeur.titre} » et ses données associées ?`,
    );
    if (!confirmation) {
      return;
    }

    this.chargementSuppression.set(true);
    this.serviceRumeur.supprimerRumeur(id).subscribe({
      next: () => {
        void this.routeur.navigate(['/rumeurs']);
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargementSuppression.set(false);
      },
      complete: () => this.chargementSuppression.set(false),
    });
  }

  private lireMessageRetour(): void {
    if (this.messagesSucces().length > 0) {
      return;
    }

    const parametres = this.route.snapshot.queryParamMap;
    if (parametres.get('cree') === '1') {
      this.messagesSucces.set([
        'Rumeur enregistrée. Vous pouvez maintenant documenter ses sources.',
      ]);
    } else if (parametres.get('publicationAjoutee') === '1') {
      this.messagesSucces.set([
        'Publication ajoutée et analysée. La liste des sources a été actualisée.',
      ]);
    }
  }
}
