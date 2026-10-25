import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'dateFrancaise',
  standalone: true,
})
export class PipeDateFrancaise implements PipeTransform {
  transform(valeur: string | Date | null | undefined, avecHeure = false): string {
    if (!valeur) {
      return '—';
    }

    const date = valeur instanceof Date ? valeur : new Date(valeur);
    if (Number.isNaN(date.getTime())) {
      return '—';
    }

    return new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      ...(avecHeure ? { hour: '2-digit', minute: '2-digit' } : {}),
    }).format(date);
  }
}
