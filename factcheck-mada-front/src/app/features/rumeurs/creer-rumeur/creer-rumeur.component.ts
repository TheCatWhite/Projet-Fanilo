import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import {
  DonneesCreationRumeur,
  LangueRumeur,
  ReponseCreationRumeur,
} from '../../../core/models/rumeur.model';
import { ServiceErreur } from '../../../core/services/service-erreur';
import { ServiceRumeur } from '../../../core/services/service-rumeur';
import { ComposantChargeur } from '../../../shared/composants/chargeur/chargeur.component';
import { ComposantMessageErreur } from '../../../shared/composants/message-erreur/message-erreur.component';

@Component({
  selector: 'app-creer-rumeur',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, ComposantChargeur, ComposantMessageErreur],
  templateUrl: './creer-rumeur.component.html',
  styleUrl: './creer-rumeur.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantCreerRumeur {
  private readonly constructeurFormulaire = inject(FormBuilder);
  private readonly serviceRumeur = inject(ServiceRumeur);
  private readonly serviceErreur = inject(ServiceErreur);
  private readonly routeur = inject(Router);

  readonly chargement = signal(false);
  readonly messagesErreur = signal<string[]>([]);
  readonly doublon = signal<ReponseCreationRumeur | null>(null);

  readonly formulaire = this.constructeurFormulaire.nonNullable.group({
    titre: ['', [Validators.required, Validators.minLength(5), Validators.maxLength(200)]],
    contenu: ['', [Validators.required, Validators.minLength(20)]],
    langue: ['fr' as LangueRumeur, [Validators.required]],
  });

  get titre() {
    return this.formulaire.controls.titre;
  }

  get contenu() {
    return this.formulaire.controls.contenu;
  }

  envoyer(): void {
    this.messagesErreur.set([]);
    this.doublon.set(null);

    if (this.formulaire.invalid) {
      this.formulaire.markAllAsTouched();
      return;
    }

    const valeurs = this.formulaire.getRawValue();
    const donnees: DonneesCreationRumeur = {
      titre: valeurs.titre.trim(),
      contenu: valeurs.contenu.trim(),
      langue: valeurs.langue,
    };

    this.chargement.set(true);
    this.serviceRumeur.creerRumeur(donnees).subscribe({
      next: (reponse) => {
        if (!reponse.cree) {
          this.doublon.set(reponse);
          this.chargement.set(false);
          return;
        }
        void this.routeur.navigate(['/rumeurs', reponse.rumeur.id], {
          queryParams: { cree: '1' },
        });
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargement.set(false);
      },
      complete: () => this.chargement.set(false),
    });
  }
}
