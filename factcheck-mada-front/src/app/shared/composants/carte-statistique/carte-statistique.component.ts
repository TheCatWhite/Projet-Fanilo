import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-carte-statistique',
  standalone: true,
  template: `
    <article class="statistique">
      <span class="statistique__libelle">{{ libelle }}</span>
      <strong class="statistique__valeur">{{ valeur }}</strong>
      @if (precision) {
        <span class="statistique__precision">{{ precision }}</span>
      }
    </article>
  `,
  styleUrl: './carte-statistique.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantCarteStatistique {
  @Input() libelle = '';
  @Input() valeur: string | number = '—';
  @Input() precision = '';
}
