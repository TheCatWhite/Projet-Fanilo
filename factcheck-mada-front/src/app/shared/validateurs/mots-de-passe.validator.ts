import { AbstractControl, ValidationErrors } from '@angular/forms';

/**
 * Vérifie que le mot de passe et sa confirmation sont identiques.
 * À appliquer sur le FormGroup d'inscription.
 */
export function validateurMotsDePasse(groupe: AbstractControl): ValidationErrors | null {
  const motDePasse = groupe.get('mot_de_passe')?.value;
  const confirmation = groupe.get('confirmation_mot_de_passe')?.value;

  if (!motDePasse || !confirmation) {
    return null;
  }

  return motDePasse === confirmation ? null : { motsDePasseDifferents: true };
}
