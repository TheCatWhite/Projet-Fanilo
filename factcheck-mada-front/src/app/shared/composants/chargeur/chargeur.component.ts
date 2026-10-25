import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-chargeur',
  standalone: true,
  template: `
    <div class="chargeur" role="status" aria-live="polite">
      <span class="chargeur__rond" aria-hidden="true"></span>
      <p>{{ message }}</p>
    </div>
  `,
  styleUrl: './chargeur.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantChargeur {
  @Input() message = 'Chargement en cours…';
}
