import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { LIBELLES_PLATEFORME, Plateforme } from '../../../core/models/publication-source.model';
import { StatistiquesTableauDeBord } from '../../../core/models/tableau-de-bord.model';
import { ServiceAuthentification } from '../../../core/services/service-authentification';
import { ServiceErreur } from '../../../core/services/service-erreur';
import { ServiceTableauDeBord } from '../../../core/services/service-tableau-de-bord';
import { ComposantBadgeRisque } from '../../../shared/composants/badge-risque/badge-risque.component';
import { ComposantCarteStatistique } from '../../../shared/composants/carte-statistique/carte-statistique.component';
import { ComposantChargeur } from '../../../shared/composants/chargeur/chargeur.component';
import { ComposantEtatVide } from '../../../shared/composants/etat-vide/etat-vide.component';
import { ComposantMessageErreur } from '../../../shared/composants/message-erreur/message-erreur.component';
import { PipeDateFrancaise } from '../../../shared/pipes/pipe-date-francaise';

@Component({
  selector: 'app-tableau-de-bord',
  standalone: true,
  imports: [
    RouterLink,
    ComposantBadgeRisque,
    ComposantCarteStatistique,
    ComposantChargeur,
    ComposantEtatVide,
    ComposantMessageErreur,
    PipeDateFrancaise,
  ],
  templateUrl: './tableau-de-bord.component.html',
  styleUrl: './tableau-de-bord.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantTableauDeBord implements OnInit {
  private readonly serviceTableauDeBord = inject(ServiceTableauDeBord);
  private readonly serviceAuthentification = inject(ServiceAuthentification);
  private readonly serviceErreur = inject(ServiceErreur);

  readonly profil = this.serviceAuthentification.profil;
  readonly chargement = signal(true);
  readonly messagesErreur = signal<string[]>([]);
  readonly statistiques = signal<StatistiquesTableauDeBord | null>(null);

  readonly repartitionPlateformes = computed(() => {
    const repartition = this.statistiques()?.repartition_plateformes ?? {};
    return Object.entries(repartition)
      .map(([cle, valeur]) => ({
        cle,
        libelle: LIBELLES_PLATEFORME[cle as Plateforme] ?? cle,
        valeur,
      }))
      .sort((a, b) => b.valeur - a.valeur);
  });

  ngOnInit(): void {
    this.charger();
  }

  charger(): void {
    this.chargement.set(true);
    this.messagesErreur.set([]);
    this.serviceTableauDeBord.obtenirStatistiques().subscribe({
      next: (statistiques) => this.statistiques.set(statistiques),
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargement.set(false);
      },
      complete: () => this.chargement.set(false),
    });
  }
}
