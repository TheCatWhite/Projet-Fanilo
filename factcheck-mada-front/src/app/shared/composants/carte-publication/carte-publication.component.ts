import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

import {
  ICONES_PLATEFORME,
  PublicationSource,
} from '../../../core/models/publication-source.model';
import { PipeDateFrancaise } from '../../pipes/pipe-date-francaise';
import { ComposantBadgeSourceZero } from '../badge-source-zero/badge-source-zero.component';
import { ComposantCarteAlerte } from '../carte-alerte/carte-alerte.component';

@Component({
  selector: 'app-carte-publication',
  standalone: true,
  imports: [PipeDateFrancaise, ComposantBadgeSourceZero, ComposantCarteAlerte],
  templateUrl: './carte-publication.component.html',
  styleUrl: './carte-publication.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantCartePublication {
  @Input({ required: true }) publication!: PublicationSource;

  get icone(): string {
    return ICONES_PLATEFORME[this.publication.plateforme] ?? '•';
  }
}
