import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter, map, startWith } from 'rxjs';

import { ServiceAuthentification } from './core/services/service-authentification';
import { ComposantBarreNavigation } from './shared/composants/barre-navigation/barre-navigation.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ComposantBarreNavigation],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantApplication {
  private readonly routeur = inject(Router);
  private readonly serviceAuthentification = inject(ServiceAuthentification);

  readonly profil = this.serviceAuthentification.profil;
  private readonly urlCourante = toSignal(
    this.routeur.events.pipe(
      filter((evenement): evenement is NavigationEnd => evenement instanceof NavigationEnd),
      map((evenement) => evenement.urlAfterRedirects),
      startWith(this.routeur.url),
    ),
    { initialValue: this.routeur.url },
  );

  readonly estPageAuthentification = computed(
    () =>
      this.urlCourante().startsWith('/connexion') || this.urlCourante().startsWith('/inscription'),
  );

  readonly afficherNavigation = computed(
    () => this.serviceAuthentification.estConnecte() && !this.estPageAuthentification(),
  );

  constructor() {
    this.serviceAuthentification.initialiserProfil();
  }

  deconnecter(): void {
    this.serviceAuthentification.deconnexion();
    void this.routeur.navigate(['/connexion']);
  }
}
