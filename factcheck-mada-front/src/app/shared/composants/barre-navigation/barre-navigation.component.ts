import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { Journaliste, LIBELLES_ROLE } from '../../../core/models/journaliste.model';

@Component({
  selector: 'app-barre-navigation',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './barre-navigation.component.html',
  styleUrl: './barre-navigation.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantBarreNavigation {
  @Input() profil: Journaliste | null = null;
  @Output() deconnexion = new EventEmitter<void>();

  get roleLibelle(): string {
    return this.profil ? LIBELLES_ROLE[this.profil.role] : '';
  }
}
