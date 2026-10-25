import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

import { NiveauRisque } from '../../../core/models/rapport-verification.model';

@Component({
  selector: 'app-badge-risque',
  standalone: true,
  template: `
    <span class="badge-risque" [class]="'badge-risque badge-risque--' + classe">
      {{ texte }}
    </span>
  `,
  styleUrl: './badge-risque.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantBadgeRisque {
  @Input() niveau: NiveauRisque | null = null;
  @Input() libelle: string | null = null;

  get classe(): string {
    return this.niveau ?? 'inconnu';
  }

  get texte(): string {
    if (this.libelle) {
      return this.libelle;
    }
    switch (this.niveau) {
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
