import { GraviteAlerte } from './alerte-compte.model';

export interface AlerteTexte {
  id: number;
  type_alerte: string;
  type_libelle: string;
  gravite: GraviteAlerte;
  gravite_libelle: string;
  expression_detectee: string;
  explication: string;
  cree_le: string;
}
