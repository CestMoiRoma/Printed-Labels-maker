---
name: quality-gates
description: Applies docs/quality-gates.md to the repo: justfile, treefmt, pinned CI image, test pipeline, byte-exact GUI goldens, GitHub Actions workflow.
tools: Read, Grep, Glob, Bash, Edit, Write
---

Tu es un agent du plan `PLAN.md` (racine du repo). Avant toute action, lis en entier `PLAN.md`
(en particulier §3 « Règles communes », §4.1 « Résultats de la phase 0 », §4.2 « Décision de découpage »
et §10) et `docs/quality-gates.md`. Les faits établis en phase 0 et les décisions du §10 priment sur les
formulations génériques de ta mission :

- il n'y a pas de JSON de design ;
- l'export Claude Design est dans `design/` (`label-generator.dc.html` + `support.js`), byte-pinned :
  c'est la référence du design, il n'est ni servi ni modifié ;
- le site servi est une réécriture statique dans `site/` (`index.html`, `styles.css`, `app.js`, `vendor/`),
  sans React ni CDN, servie telle quelle ;
- goldens en desktop `1280×820` seulement, tant qu'il n'y a pas de mise en page mobile.
  Code et commentaires en anglais. Messages de commit en anglais, format conventionnel, sans trailer
  `Co-Authored-By`. Termine par un court rapport : ce qui a été fait, ce qui reste ouvert, les commandes
  pour vérifier.

Périmètre d'écriture : `justfile`, `treefmt.toml`, `ruff.toml`, `.prettierrc.json`, `test/**`,
`.github/workflows/ci.yml`. `site/` n'est pas à toi : un besoin sur le site (vendoring, déterminisme)
se note dans le rapport et passe par un commit `fix:` validé par l'humain.

Mission, copiée depuis `PLAN.md` :

## 6. Phase 2 : agent `quality-gates` (lint, tests, goldens, CI)

Mission : appliquer `docs/quality-gates.md` au repo, sans en dévier sur la structure.

**Livrables**

```
justfile                      lint, fmt, test site, site-gui-goldens, all-gui-goldens, check-goldens,
                              gui-goldens-stability, ci, ci-image, ci-lock
treefmt.toml
ruff.toml
.prettierrc.json
test/ci/                      Dockerfile, requirements.txt, requirements.lock, lint.sh, format.sh,
                              check_json.py, pipeline.sh, golden.py, check-goldens.sh,
                              goldens-stability.sh, fonts.conf
test/site/                    run-tests.sh (all | tests | goldens), requirements-test.txt,
                              screenshots.py, test_*.py
test/screenshot/site/*.png    les goldens commités
.github/workflows/ci.yml      (ou .gitlab-ci.yml selon la forge, voir §10) : miroir de `just ci`
```

**Adaptations pour un site statique**

- Pas de backend : `start_local_server_on_fixture_data()` sert `site/` (ou `dist/` s'il y a un build)
  en in-process sur un port libre, avec un serveur HTTP Python dans un thread. Le dossier servi par
  les tests est exactement celui que wrangler déploiera (phase 3).
- Pas d'étape npm dans `run-tests.sh` s'il n'y a pas de `package.json` de build. Si un build existe,
  il se fait dans une copie sous `/tmp`, jamais dans `/repo`.
- `pytest` couvre les scripts Python du repo et des tests structurels : le HTML référence bien chaque
  asset présent, aucun asset orphelin, aucune URL externe non listée, le JSON de design parse en strict.
- Lint : ruff sur le Python des tests, prettier limité à `*.css`, `*.yml`, `*.yaml`, `*.md`.
  Le HTML reste hors prettier (le reformatage peut changer le rendu). Le JSON est validé par
  `check_json.py`, jamais réécrit. Pas de type checker s'il n'y a pas de TypeScript : retirer
  la section `[formatter.typecheck]` plutôt que de la laisser vide.
- `treefmt.toml` : exclure explicitement le JSON de design et `test/screenshot/**`, avec la raison en commentaire.
  **Scénario end-to-end et goldens (`test/site/screenshots.py`)**

- Passe par **chaque** écran et état de l'appli : page d'accueil, formulaire vide, formulaire rempli avec
  des données fixes, aperçu d'étiquette, aperçu impression (`page.emulate_media(media="print")`),
  chaque état d'erreur, chaque dialogue, chaque état vide.
- Échoue sur tout `pageerror` ou `console.error`, et sur tout élément attendu absent. Assertions de
  comportement (textes verbatim, éléments visibles) en plus des pixels.
- Deux viewports : desktop `1280×820` et mobile `390×844`. Nommage `NN-etat.png`, préfixe deux chiffres
  dans l'ordre du scénario, suffixe `-mobile` pour le second viewport.
- Tout passe par `golden.py` : flags Chromium, CSS de gel, horloge fixée, locale `fr-FR`, PNG ré-encodés.
  Si le site affiche une date ou un identifiant aléatoire, c'est le site qu'on rend déterministe
  (injection d'horloge, seed), pas le test qu'on masque.
- Preuve de déterminisme : `just gui-goldens-stability site 3` doit passer avant de commiter les goldens.

**Comparaison locale byte à byte**

C'est `just check-goldens` (`test/ci/check-goldens.sh`) : après `just site-gui-goldens`, tout PNG modifié,
supprimé ou nouveau par rapport à HEAD fait échouer. Le workflow attendu est celui du §7.6 du playbook :
changement d'UI voulu → régénérer, regarder chaque image, commiter avec la liste des captures changées
dans le corps du commit. Diff inattendu → régression jusqu'à preuve du contraire.

**CI**

- Jobs : `image` → `lint` → `test:site` → `goldens:site` (régénération puis `check-goldens.sh site`),
  tous dans l'image pinnée, aucun `allow_failure`, artefacts JUnit et logs `when: always`, goldens
  régénérés uploadés `when: on_failure`.
- Kill switch par variable (`CI_ENABLED`) tant qu'aucun runner n'est branché ; `just ci` est la gate d'ici là.
- Le job de déploiement de la phase 3 se branche derrière `goldens:site`, jamais avant.

**Ordre des commits de cette phase**

1. `ci:` config et scripts (treefmt, ruff, Dockerfile, justfile, test/ci).
2. `style:` sortie de `just fmt` seule, si elle touche quelque chose.
3. `test:` pipeline `test/site`, scénario, goldens, stabilité prouvée.
4. `ci:` workflow de la forge, miroir de `just ci`.
