import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { debounceTime } from 'rxjs';

import { FiltresRumeurs, RumeurListe, StatutRumeur } from '../../../core/models/rumeur.model';
import { ServiceErreur } from '../../../core/services/service-erreur';
import { ServiceRumeur } from '../../../core/services/service-rumeur';
import { ComposantBadgeRisque } from '../../../shared/composants/badge-risque/badge-risque.component';
import { ComposantChargeur } from '../../../shared/composants/chargeur/chargeur.component';
import { ComposantEtatVide } from '../../../shared/composants/etat-vide/etat-vide.component';
import { ComposantMessageErreur } from '../../../shared/composants/message-erreur/message-erreur.component';
import { PipeDateFrancaise } from '../../../shared/pipes/pipe-date-francaise';

@Component({
  selector: 'app-liste-rumeurs',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    ComposantBadgeRisque,
    ComposantChargeur,
    ComposantEtatVide,
    ComposantMessageErreur,
    PipeDateFrancaise,
  ],
  templateUrl: './liste-rumeurs.component.html',
  styleUrl: './liste-rumeurs.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantListeRumeurs implements OnInit {
  private readonly constructeurFormulaire = inject(FormBuilder);
  private readonly serviceRumeur = inject(ServiceRumeur);
  private readonly serviceErreur = inject(ServiceErreur);
  private readonly destroyRef = inject(DestroyRef);

  readonly taillePage = 10;
  readonly chargement = signal(true);
  readonly messagesErreur = signal<string[]>([]);
  readonly resultats = signal<RumeurListe[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);

  readonly formulaire = this.constructeurFormulaire.nonNullable.group({
    recherche: '',
    statut: '' as StatutRumeur | '',
  });

  readonly nombrePages = computed(() => Math.max(1, Math.ceil(this.total() / this.taillePage)));

  constructor() {
    this.formulaire.valueChanges
      .pipe(debounceTime(350), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.charger(1));
  }

  ngOnInit(): void {
    this.charger(1);
  }

  charger(page = 1): void {
    this.page.set(page);
    this.chargement.set(true);
    this.messagesErreur.set([]);

    const valeurs = this.formulaire.getRawValue();
    const filtres: FiltresRumeurs = {
      page,
      taille_page: this.taillePage,
      recherche: valeurs.recherche,
      statut: valeurs.statut || undefined,
    };

    this.serviceRumeur.obtenirRumeurs(filtres).subscribe({
      next: (reponse) => {
        this.resultats.set(reponse.resultats);
        this.total.set(reponse.total);
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargement.set(false);
      },
      complete: () => this.chargement.set(false),
    });
  }

  reinitialiser(): void {
    this.formulaire.reset({ recherche: '', statut: '' });
  }

  pagePrecedente(): void {
    if (this.page() > 1) {
      this.charger(this.page() - 1);
    }
  }

  pageSuivante(): void {
    if (this.page() < this.nombrePages()) {
      this.charger(this.page() + 1);
    }
  }
}
