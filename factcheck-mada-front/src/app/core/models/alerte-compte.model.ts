export type GraviteAlerte = 'faible' | 'moyenne' | 'elevee';

export interface AlerteCompte {
  id: number;
  type_alerte: string;
  type_libelle: string;
  gravite: GraviteAlerte;
  gravite_libelle: string;
  description: string;
  cree_le: string;
}
