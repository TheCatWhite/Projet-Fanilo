import { expect, test } from '@playwright/test';

async function seConnecter(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/connexion');
  await page.locator('#nom_utilisateur').fill('demo');
  await page.locator('#mot_de_passe').fill('Demo1234!');
  await Promise.all([
    page.waitForURL('**/tableau-de-bord'),
    page.locator('button[type="submit"]').click(),
  ]);
}

test('parcours journaliste : connexion, rumeurs, propagation et rapport', async ({ page }) => {
  await seConnecter(page);
  await expect(page.getByRole('heading', { name: /Bonjour/ })).toBeVisible();
  await expect(page.locator('.statistique')).toHaveCount(4);

  await page.getByRole('link', { name: 'Rumeurs', exact: true }).click();
  await expect(page).toHaveURL(/\/rumeurs$/);
  await expect(page.getByRole('heading', { name: 'Rumeurs', exact: true })).toBeVisible();
  await expect(page.locator('.rumeur-carte').first()).toBeVisible();

  await page.locator('.rumeur-carte h2 a').first().click();
  await expect(page).toHaveURL(/\/rumeurs\/\d+$/);
  await expect(page.getByRole('heading', { name: 'Source Zéro', exact: true })).toBeVisible();

  await page.getByRole('link', { name: 'Voir la propagation' }).click();
  await expect(page).toHaveURL(/\/rumeurs\/\d+\/propagation$/);
  await expect(page.getByRole('heading', { name: 'Propagation', exact: true })).toBeVisible();

  await page.getByRole('link', { name: 'Retour au dossier' }).click();
  await expect(page).toHaveURL(/\/rumeurs\/\d+$/);

  await page
    .locator('.dossier__actions')
    .getByRole('link', { name: 'Fiche de vérification' })
    .click();
  await expect(page).toHaveURL(/\/rumeurs\/\d+\/rapport$/);
  await expect(
    page.getByRole('heading', { name: 'Fiche de vérification', exact: true }),
  ).toBeVisible();

  const couverture = page.locator('.rapport__couverture');
  await expect(page.locator('.rapport__couverture, .rapport__sans-fiche')).toBeVisible({
    timeout: 20_000,
  });
  if (!(await couverture.isVisible().catch(() => false))) {
    await page.locator('.rapport__sans-fiche button').click();
  }
  await expect(couverture).toBeVisible({ timeout: 45_000 });
  await expect(
    page.getByText('Analyse automatique — vérification humaine requise').first(),
  ).toBeVisible();

  const promesseTelechargement = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Télécharger le PDF' }).click();
  const telechargement = await promesseTelechargement;
  expect(telechargement.suggestedFilename()).toContain('rapport-verification');
  expect(telechargement.suggestedFilename()).toContain('.pdf');

  await page.getByRole('button', { name: 'Déconnexion' }).click();
  await expect(page).toHaveURL(/\/connexion$/);
});

test('affiche une erreur avec de mauvais identifiants', async ({ page }) => {
  await page.goto('/connexion');
  await page.locator('#nom_utilisateur').fill('demo');
  await page.locator('#mot_de_passe').fill('mauvais-mot-de-passe');
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('.message--erreur')).toBeVisible();
  await expect(page).toHaveURL(/\/connexion$/);
});

test('crée puis supprime une rumeur de test', async ({ page }) => {
  await seConnecter(page);
  const titre = `Rumeur E2E ${Date.now()}`;

  await page.getByRole('main').getByRole('link', { name: 'Nouvelle rumeur' }).click();
  await expect(page).toHaveURL(/\/rumeurs\/nouvelle$/);
  await page.locator('#titre').fill(titre);
  await page
    .locator('#contenu')
    .fill(
      'Cette affirmation de test est suffisamment longue pour être enregistrée par le backend.',
    );
  await page.getByRole('button', { name: 'Enregistrer la rumeur' }).click();

  await expect(page).toHaveURL(/\/rumeurs\/\d+\?cree=1$/);
  await expect(page.getByRole('heading', { name: titre })).toBeVisible();
  await expect(page.getByText('Rumeur enregistrée.')).toBeVisible();

  page.once('dialog', async (dialogue) => {
    expect(dialogue.message()).toContain('Supprimer définitivement');
    await dialogue.accept();
  });
  await page.locator('.dossier__actions').getByRole('button', { name: 'Supprimer' }).click();
  await expect(page).toHaveURL(/\/rumeurs$/);
  await expect(page.getByRole('heading', { name: 'Rumeurs', exact: true })).toBeVisible();
});
