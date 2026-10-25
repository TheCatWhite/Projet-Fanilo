import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { DonneesInscription } from '../../../core/models/authentification.model';
import { ServiceAuthentification } from '../../../core/services/service-authentification';
import { ServiceErreur } from '../../../core/services/service-erreur';
import { ComposantChargeur } from '../../../shared/composants/chargeur/chargeur.component';
import { ComposantMessageErreur } from '../../../shared/composants/message-erreur/message-erreur.component';
import { validateurMotsDePasse } from '../../../shared/validateurs/mots-de-passe.validator';

@Component({
  selector: 'app-inscription',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    ComposantChargeur,
    ComposantMessageErreur,
  ],
  templateUrl: './inscription.component.html',
  styleUrl: './inscription.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantInscription {
  private readonly constructeurFormulaire = inject(FormBuilder);
  private readonly serviceAuthentification = inject(ServiceAuthentification);
  private readonly serviceErreur = inject(ServiceErreur);
  private readonly routeur = inject(Router);

  readonly chargement = signal(false);
  readonly messagesErreur = signal<string[]>([]);

  readonly formulaire = this.constructeurFormulaire.nonNullable.group(
    {
      nom_utilisateur: [
        '',
        [
          Validators.required,
          Validators.minLength(3),
          Validators.maxLength(150),
        ],
      ],
      email: ['', [Validators.required, Validators.email]],
      mot_de_passe: [
        '',
        [Validators.required, Validators.minLength(8)],
      ],
      confirmation_mot_de_passe: [
        '',
        [Validators.required, Validators.minLength(8)],
      ],
      redaction: ['', [Validators.maxLength(150)]],
    },
    { validators: validateurMotsDePasse },
  );

  get nomUtilisateur() {
    return this.formulaire.controls.nom_utilisateur;
  }

  get email() {
    return this.formulaire.controls.email;
  }

  get motDePasse() {
    return this.formulaire.controls.mot_de_passe;
  }

  get confirmationMotDePasse() {
    return this.formulaire.controls.confirmation_mot_de_passe;
  }

  get redaction() {
    return this.formulaire.controls.redaction;
  }

  envoyer(): void {
    this.messagesErreur.set([]);

    if (this.formulaire.invalid) {
      this.formulaire.markAllAsTouched();
      return;
    }

    this.chargement.set(true);
    const valeurs = this.formulaire.getRawValue();
    const donnees: DonneesInscription = {
      nom_utilisateur: valeurs.nom_utilisateur.trim(),
      email: valeurs.email.trim(),
      mot_de_passe: valeurs.mot_de_passe,
      confirmation_mot_de_passe: valeurs.confirmation_mot_de_passe,
      redaction: valeurs.redaction.trim(),
    };

    this.serviceAuthentification.inscription(donnees).subscribe({
      next: () => {
        void this.routeur.navigate(['/tableau-de-bord']);
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargement.set(false);
      },
      complete: () => this.chargement.set(false),
    });
  }
}
