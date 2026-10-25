import { ChangeDetectionStrategy, Component } from '@angular/core';

@Component({
  selector: 'app-badge-source-zero',
  standalone: true,
  template: `<span class="badge-source">Source Zéro détectée</span>`,
  styleUrl: './badge-source-zero.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantBadgeSourceZero {}
