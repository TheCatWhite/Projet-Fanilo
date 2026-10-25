import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

import { GraviteAlerte } from '../../../core/models/alerte-compte.model';

@Component({
  selector: 'app-carte-alerte',
  standalone: true,
  template: `
    <article class="alerte" [class]="'alerte alerte--' + gravite">
      <div class="alerte__entete">
        <strong>{{ typeLibelle }}</strong>
        <span class="alerte__gravite">{{ gravite }}</span>
      </div>
      @if (expression) {
        <p class="alerte__expression">« {{ expression }} »</p>
      }
      <p class="alerte__description">{{ description }}</p>
      @if (explication) {
        <p class="alerte__explication">{{ explication }}</p>
      }
    </article>
  `,
  styleUrl: './carte-alerte.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantCarteAlerte {
  @Input() typeLibelle = '';
  @Input() gravite: GraviteAlerte = 'moyenne';
  @Input() description = '';
  @Input() expression = '';
  @Input() explication = '';
}
