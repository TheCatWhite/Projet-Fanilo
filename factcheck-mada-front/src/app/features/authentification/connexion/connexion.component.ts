import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ServiceAuthentification } from '../../../core/services/service-authentification';
import { ServiceErreur } from '../../../core/services/service-erreur';
import { ComposantChargeur } from '../../../shared/composants/chargeur/chargeur.component';
import { ComposantMessageErreur } from '../../../shared/composants/message-erreur/message-erreur.component';

@Component({
  selector: 'app-connexion',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, ComposantChargeur, ComposantMessageErreur],
  templateUrl: './connexion.component.html',
  styleUrl: './connexion.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantConnexion {
  private readonly constructeurFormulaire = inject(FormBuilder);
  private readonly serviceAuthentification = inject(ServiceAuthentification);
  private readonly serviceErreur = inject(ServiceErreur);
  private readonly routeur = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly chargement = signal(false);
  readonly messagesErreur = signal<string[]>([]);

  readonly formulaire = this.constructeurFormulaire.nonNullable.group({
    nom_utilisateur: ['', [Validators.required]],
    mot_de_passe: ['', [Validators.required]],
  });

  get nomUtilisateur() {
    return this.formulaire.controls.nom_utilisateur;
  }

  get motDePasse() {
    return this.formulaire.controls.mot_de_passe;
  }

  envoyer(): void {
    this.messagesErreur.set([]);

    if (this.formulaire.invalid) {
      this.formulaire.markAllAsTouched();
      return;
    }

    this.chargement.set(true);
    this.serviceAuthentification.connexion(this.formulaire.getRawValue()).subscribe({
      next: () => {
        const retour = this.route.snapshot.queryParamMap.get('retour');
        const destination =
          retour && retour.startsWith('/') && !retour.startsWith('//')
            ? retour
            : '/tableau-de-bord';
        void this.routeur.navigateByUrl(destination);
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargement.set(false);
      },
      complete: () => this.chargement.set(false),
    });
  }
}
