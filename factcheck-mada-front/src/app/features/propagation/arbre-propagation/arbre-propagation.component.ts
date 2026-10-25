import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { ArbrePropagation, LienArbre } from '../../../core/models/arbre-propagation.model';
import { LIBELLES_PLATEFORME, Plateforme } from '../../../core/models/publication-source.model';
import { ServiceAnalyse } from '../../../core/services/service-analyse';
import { ServiceErreur } from '../../../core/services/service-erreur';
import { ComposantBadgeSourceZero } from '../../../shared/composants/badge-source-zero/badge-source-zero.component';
import { ComposantCarteStatistique } from '../../../shared/composants/carte-statistique/carte-statistique.component';
import { ComposantChargeur } from '../../../shared/composants/chargeur/chargeur.component';
import { ComposantEtatVide } from '../../../shared/composants/etat-vide/etat-vide.component';
import { ComposantMessageErreur } from '../../../shared/composants/message-erreur/message-erreur.component';
import { PipeDateFrancaise } from '../../../shared/pipes/pipe-date-francaise';

@Component({
  selector: 'app-arbre-propagation',
  standalone: true,
  imports: [
    RouterLink,
    ComposantBadgeSourceZero,
    ComposantCarteStatistique,
    ComposantChargeur,
    ComposantEtatVide,
    ComposantMessageErreur,
    PipeDateFrancaise,
  ],
  templateUrl: './arbre-propagation.component.html',
  styleUrl: './arbre-propagation.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantArbrePropagation {
  private readonly route = inject(ActivatedRoute);
  private readonly serviceAnalyse = inject(ServiceAnalyse);
  private readonly serviceErreur = inject(ServiceErreur);

  readonly rumeurId = Number(this.route.snapshot.paramMap.get('id'));
  readonly chargement = signal(true);
  readonly messagesErreur = signal<string[]>([]);
  readonly arbre = signal<ArbrePropagation | null>(null);

  readonly noeudsTries = computed(() =>
    [...(this.arbre()?.noeuds ?? [])].sort(
      (a, b) => new Date(a.date_publication).getTime() - new Date(b.date_publication).getTime(),
    ),
  );

  readonly liensParEnfant = computed(() => {
    const liens = new Map<number, LienArbre>();
    for (const lien of this.arbre()?.liens ?? []) {
      liens.set(lien.publication_enfant_id, lien);
    }
    return liens;
  });

  readonly repartitionPlateformes = computed(() =>
    Object.entries(this.arbre()?.statistiques_propagation.repartition_plateformes ?? {})
      .map(([cle, valeur]) => ({
        cle,
        libelle: LIBELLES_PLATEFORME[cle as Plateforme] ?? cle,
        valeur,
      }))
      .sort((a, b) => b.valeur - a.valeur),
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
    this.serviceAnalyse.obtenirArbrePropagation(this.rumeurId).subscribe({
      next: (arbre) => this.arbre.set(arbre),
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargement.set(false);
      },
      complete: () => this.chargement.set(false),
    });
  }

  lienPour(noeudId: number): LienArbre | undefined {
    return this.liensParEnfant().get(noeudId);
  }

  scoreEnPourcentage(lien: LienArbre | undefined): string {
    if (!lien) {
      return '';
    }
    return `${Math.round(lien.score_similarite * 100)} %`;
  }
}
