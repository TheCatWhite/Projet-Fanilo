/**
 * Configuration de l'application pour le développement local.
 *
 * Le backend Django autorise l'origine http://localhost:5173. Le serveur
 * Angular est donc configuré sur ce port dans angular.json.
 */
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/',
  nomApplication: 'FactCheck Mada',
};
