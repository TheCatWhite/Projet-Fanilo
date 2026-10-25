import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'app-etat-vide',
  standalone: true,
  template: `
    <div class="etat-vide">
      <p>{{ message }}</p>
      <ng-content />
    </div>
  `,
  styleUrl: './etat-vide.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantEtatVide {
  @Input() message = 'Aucun élément à afficher.';
}
