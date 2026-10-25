import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import {
  DonneesPublication,
  LIBELLES_PLATEFORME,
  Plateforme,
} from '../../../core/models/publication-source.model';
import { ServiceErreur } from '../../../core/services/service-erreur';
import { ServicePublication } from '../../../core/services/service-publication';
import { ComposantChargeur } from '../../../shared/composants/chargeur/chargeur.component';
import { ComposantMessageErreur } from '../../../shared/composants/message-erreur/message-erreur.component';

const TAILLE_MAX_CAPTURE = 5 * 1024 * 1024;
const EXTENSIONS_IMAGES = ['.jpg', '.jpeg', '.png', '.webp', '.gif'];

@Component({
  selector: 'app-ajouter-publication',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    ComposantChargeur,
    ComposantMessageErreur,
  ],
  templateUrl: './ajouter-publication.component.html',
  styleUrl: './ajouter-publication.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantAjouterPublication {
  private readonly constructeurFormulaire = inject(FormBuilder);
  private readonly servicePublication = inject(ServicePublication);
  private readonly serviceErreur = inject(ServiceErreur);
  private readonly route = inject(ActivatedRoute);
  private readonly routeur = inject(Router);

  readonly plateformes = Object.entries(LIBELLES_PLATEFORME) as [
    Plateforme,
    string,
  ][];
  readonly chargement = signal(false);
  readonly messagesErreur = signal<string[]>([]);
  readonly fichierSelectionne = signal<File | null>(null);
  readonly nomFichier = signal('');
  readonly rumeurId = Number(this.route.snapshot.paramMap.get('id'));

  readonly formulaire = this.constructeurFormulaire.nonNullable.group({
    plateforme: ['facebook' as Plateforme, [Validators.required]],
    nom_auteur: ['', [Validators.required, Validators.maxLength(150)]],
    url_publication: [''],
    url_profil_auteur: [''],
    date_creation_compte: [''],
    nombre_abonnes: [null as number | null],
    date_publication: [this.dateHeureLocale(), [Validators.required]],
    texte_brut: [''],
  });

  get nomAuteur() {
    return this.formulaire.controls.nom_auteur;
  }

  get datePublication() {
    return this.formulaire.controls.date_publication;
  }

  surFichierSelectionne(evenement: Event): void {
    const input = evenement.target as HTMLInputElement;
    const fichier = input.files?.[0] ?? null;
    this.messagesErreur.set([]);

    if (!fichier) {
      this.fichierSelectionne.set(null);
      this.nomFichier.set('');
      return;
    }

    if (fichier.size > TAILLE_MAX_CAPTURE) {
      this.messagesErreur.set(['La capture d’écran ne doit pas dépasser 5 Mo.']);
      input.value = '';
      return;
    }

    const extension = fichier.name.slice(fichier.name.lastIndexOf('.')).toLowerCase();
    if (!EXTENSIONS_IMAGES.includes(extension)) {
      this.messagesErreur.set([
        'Format d’image non accepté. Utilisez JPG, PNG, WEBP ou GIF.',
      ]);
      input.value = '';
      return;
    }

    this.fichierSelectionne.set(fichier);
    this.nomFichier.set(fichier.name);
  }

  envoyer(): void {
    this.messagesErreur.set([]);

    if (!Number.isInteger(this.rumeurId) || this.rumeurId <= 0) {
      this.messagesErreur.set(['Identifiant de rumeur invalide.']);
      return;
    }

    if (this.formulaire.invalid) {
      this.formulaire.markAllAsTouched();
      return;
    }

    const valeurs = this.formulaire.getRawValue();
    const donnees: DonneesPublication = {
      plateforme: valeurs.plateforme,
      nom_auteur: valeurs.nom_auteur.trim(),
      date_publication: this.convertirEnIso(valeurs.date_publication),
      url_publication: valeurs.url_publication.trim(),
      url_profil_auteur: valeurs.url_profil_auteur.trim(),
      date_creation_compte: valeurs.date_creation_compte || undefined,
      nombre_abonnes:
        valeurs.nombre_abonnes === null
          ? null
          : Number(valeurs.nombre_abonnes),
      texte_brut: valeurs.texte_brut.trim(),
      capture_ecran: this.fichierSelectionne(),
    };

    this.chargement.set(true);
    this.servicePublication.ajouterPublication(this.rumeurId, donnees).subscribe({
      next: () => {
        void this.routeur.navigate(['/rumeurs', this.rumeurId], {
          queryParams: { publicationAjoutee: '1' },
        });
      },
      error: (erreur: unknown) => {
        this.messagesErreur.set(this.serviceErreur.extraireMessages(erreur));
        this.chargement.set(false);
      },
      complete: () => this.chargement.set(false),
    });
  }

  private dateHeureLocale(): string {
    const maintenant = new Date();
    const local = new Date(maintenant.getTime() - maintenant.getTimezoneOffset() * 60_000);
    return local.toISOString().slice(0, 16);
  }

  private convertirEnIso(valeur: string): string {
    const date = new Date(valeur);
    return Number.isNaN(date.getTime()) ? valeur : date.toISOString();
  }
}
