# Plan Claude Code : Printed Labels Maker

Ce fichier est le plan d'exécution. Il se dépose à la racine du repo avec `docs/quality-gates.md`
(le playbook lint / tests / goldens), et se lance avec le prompt de démarrage en fin de fichier.

## 1. Contexte

- Repo : Printed Labels Maker, un site web (générateur d'étiquettes à imprimer).
- Entrées : un fichier HTML et un fichier JSON exportés de Claude Design. Le JSON contient les tokens
  et la structure du design ; il est **byte-pinned** : jamais reformaté, seulement validé.
  **Constat phase 0 : l'export ne contient pas de JSON. Voir §4.1.**
- Cible d'hébergement : Cloudflare Workers (assets statiques, worker minimal seulement si nécessaire).
- Référence obligatoire pour tout ce qui touche au lint, aux tests et aux screenshots : `docs/quality-gates.md`.
  La structure du playbook est non négociable (une image Docker pinnée, un point d'entrée par gate,
  modes `all | tests | goldens`, goldens byte-exacts, `just ci` = CI).
  Placeholders du playbook à remplacer partout :

| Placeholder | Valeur                                                                          |
| ----------- | ------------------------------------------------------------------------------- |
| `<project>` | `printed-labels-maker`                                                          |
| `<app>`     | `site`                                                                          |
| `<App>`     | `site/` (dossier du site servi tel quel ; adapter si le repo a déjà un dossier) |

## 2. Ordre d'exécution

Les phases s'enchaînent, chacune part d'un repo propre et se termine par un ou plusieurs commits dédiés.

| Phase | Agent                | Sortie                                                                               |
| ----- | -------------------- | ------------------------------------------------------------------------------------ |
| 0     | (session principale) | Repérage, arborescence cible, `.claude/agents/`                                      |
| 1     | `reviewer`           | `docs/review.md`, aucune modification de code                                        |
| 2a    | `quality-gates`      | justfile, treefmt, Dockerfile CI, scripts `test/ci/`, squelette `test/site/` (§4.3)  |
| 2b    | (session principale) | vendoring, réécriture statique de `site/`, preuve de fidélité, `fix:` validés (§4.3) |
| 2c    | `quality-gates`      | scénario e2e complet, goldens, stabilité, workflow GitHub Actions (§4.3)             |
| 3     | `cloudflare`         | wrangler, recettes `dev` / `deploy`, job de déploiement                              |
| 4     | `readme`             | `README.md`                                                                          |
| 5     | (session principale) | `just ci` vert, `CLAUDE.md`, rapport final                                           |

Le reviewer passe **avant** les autres : ses findings bloquants sont corrigés (ou explicitement reportés)
avant de figer les goldens, sinon on commite des captures d'un design qu'on va retoucher.

## 3. Règles communes à tous les agents

- Un agent, un périmètre. Un agent ne touche pas aux fichiers d'un autre ; il note le besoin dans son rapport.
- Commits séparés par phase, messages en anglais au format conventionnel (`feat:`, `ci:`, `docs:`, `style:`, `fix:`).
- Le HTML et le JSON de design ne sont jamais modifiés silencieusement. Toute correction proposée par le
  reviewer est listée, l'humain valide, puis la modification se fait dans un commit `fix:` à part.
- Rien ne tourne sur l'hôte pour lint / tests / screenshots : toujours l'image `test/ci/Dockerfile`.
- Pas de test désactivé, pas de tolérance visuelle, pas d'`allow_failure`. Un outil manquant fait échouer, pas sauter.
- Code et commentaires en anglais. Voir §9 pour la langue du README.
- Chaque agent termine par un court rapport : ce qui a été fait, ce qui reste ouvert, les commandes pour vérifier.

## 4. Phase 0 : repérage et définition des agents

1. Lire en entier : le HTML, le JSON, `docs/quality-gates.md`, et l'arborescence existante.
2. Décider le nom réel des fichiers d'entrée et le dossier cible (`site/`), et l'inscrire dans ce plan.
3. Si le HTML de Claude Design embarque du CSS et du JS inline, décider s'il est éclaté en
   `site/index.html`, `site/styles.css`, `site/app.js`. Par défaut : oui, éclaté, pour que les gates
   (prettier sur le CSS, review lisible) aient prise. Le rendu doit rester au pixel près, ce que les
   goldens de la phase 2 prouveront.
4. Créer les quatre agents dans `.claude/agents/`, un fichier Markdown chacun avec frontmatter :

```markdown
---
name: reviewer
description: Reviews the code and the design fidelity of the Printed Labels Maker site. Read-only.
tools: Read, Grep, Glob, Bash
---
<mission de l'agent, copiée depuis le §5 de PLAN.md>
```

Même forme pour `quality-gates`, `cloudflare` et `readme`, avec les outils d'écriture (`Edit`, `Write`)
en plus. La mission de chaque agent est le paragraphe correspondant de ce plan, copié tel quel.

### 4.1 Résultats de la phase 0 (2026-09-18)

**Arborescence au départ.** Un commit (`README.md` d'une ligne), trois fichiers non suivis :
`Générateur d'étiquettes.dc.html` (81 454 o), `support.js` (69 150 o), `quality-gates.md`.
Remote : `git@github.com:CestMoiRoma/Printed-Labels-maker.git` (GitHub).

**Fichiers d'entrée retenus** (déplacés à l'octet près, SHA-256 vérifiés avant / après). Après la
décision du §4.2, l'export n'est plus le site servi : il reste dans `design/` comme référence de design,
byte-pinned, et `site/` accueille la réécriture statique.

| Avant                             | Après                            | SHA-256                                                            |
| --------------------------------- | -------------------------------- | ------------------------------------------------------------------ |
| `Générateur d'étiquettes.dc.html` | `design/label-generator.dc.html` | `ac741acabb9e679ee740c5a07a4e5fd3155eb31106118e55179e493b5c958be6` |
| `support.js`                      | `design/support.js`              | `8fe7df74405f3c55f49b7249c74ea1397e65d07dea2b1bd3b4a489bec2e28cbe` |
| `quality-gates.md`                | `docs/quality-gates.md`          | inchangé                                                           |

Le runtime nomme le document d'après son chemin ; servi en `/`, il prend le nom `Root`, ce qui ne change
rien au rendu. Le nom accentué avec apostrophe est abandonné : il n'a pas sa place dans une URL.

**Pas de JSON de design.** L'export Claude Design ne contient que le HTML et son runtime. Les tokens
(couleurs, rayons, espacements, typo) sont écrits en dur dans les attributs `style` du HTML. Le seul
JSON présent est l'attribut `data-props` du script de logique (schéma des props : `startMode`,
`showSheetPreview`, `defaultFont`). Conséquences :

- ce qui est byte-pinned, c'est le dossier `design/` (export de design et runtime généré, en-tête
  « do not edit ») ; il est exclu des formateurs ;
- la revue « fidélité au JSON » du reviewer devient une revue de cohérence interne : extraire la palette
  et les échelles réellement utilisées, et lister les valeurs isolées ou quasi-doublons ;
- `check_json.py` reste en place pour les JSON du repo (`package.json`, `wrangler.jsonc` exclu car JSONC).

**Nature du HTML.** Ce n'est pas une page statique mais un « Design Component » Claude Design :

- template dans `<x-dc>` avec liaisons `{{ … }}`, `<sc-for>`, `<sc-if>`, et un bloc `<helmet>` pour le `<head>` ;
- logique dans `<script type="text/x-dc" data-dc-script>` : `class Component extends DCLogic`, évaluée
  par `new Function` dans `support.js` (donc CSP avec `'unsafe-eval'` tant qu'on garde ce runtime) ;
- quasiment tout le style est en attributs `style="…"` inline, souvent avec des liaisons dynamiques ;
  le seul `<style>` fait dix lignes (dans `<helmet>`).

**Dépendances externes au runtime** (toutes chargées depuis un CDN, rien n'est local) :

- `support.js` : React 18.3.1 et ReactDOM 18.3.1 depuis unpkg (avec SRI), Babel standalone 7.29.0
  (seulement pour des imports JSX, non utilisés ici) ;
- `index.html` : `qrcode-svg@1.1.0` (jsdelivr), `@mdi/js@7.4.47` (import dynamique, jsdelivr),
  `@material-symbols/svg-400` (un fetch par icône, jsdelivr), Google Fonts (Public Sans, JetBrains Mono,
  puis la police d'étiquette chargée à la demande parmi 24 familles).
- `support.js` expose un point d'accroche : `window.__resources` (URL CDN → URL locale), défini avant le
  chargement du runtime. Il couvre React, ReactDOM et Babel sans toucher au runtime, et désactive au
  passage le `fetch(location.href)` de rechargement du template. Il ne couvre pas le reste : les
  `<script>` / `<link>` du `<helmet>` sont recopiés avec leur URL d'origine (sauf blob pré-chargé),
  et l'`import()` de mdi, le `fetch` des Material Symbols et le `<link>` Google Fonts de `loadFont()`
  sont des URL écrites en dur dans la logique. Les servir en local imposerait de modifier l'export
  (argument de plus pour la réécriture du §4.2).

**Sources de non-déterminisme repérées** (pour la phase 2) : langue détectée via `navigator.language`
(fixée par la locale `fr-FR` du contexte), polices chargées de façon asynchrone (état `fontReady`),
mesure du texte au canvas (dépend des polices installées), CDN en réseau. Aucune date ni aléa à l'écran :
la date des étiquettes de démo est la chaîne fixe `09/2026`.

**Mise en page.** Barre latérale fixe de 340 px + zone principale, sans aucune media query d'écran.
Le viewport mobile `390×844` affichera donc une mise en page non prévue.

### 4.2 Décision de découpage (étape 3)

**Décidé (2026-09-18) : réécriture statique.** Le site servi est réécrit sans React ni runtime Claude
Design : `site/index.html`, `site/styles.css`, `site/app.js`, et `site/vendor/` pour ce qui ne peut pas
être réécrit (générateur de QR, icônes mdi et Material Symbols retenues, polices en woff2 avec leur CSS).
Aucune ressource n'est chargée depuis un CDN, ni en test ni en production. Plus besoin de `'unsafe-eval'`.

L'export d'origine reste dans `design/` (`label-generator.dc.html` + `support.js`), à l'octet près :
c'est la référence du design (tokens, textes des sept langues, comportements). Il n'est ni servi ni
formaté.

Ce que ça change dans l'ordre des phases :

- le reviewer (phase 1) revoit l'export de `design/` : ses findings deviennent le cahier des charges
  de la réécriture ;
- la réécriture est faite par la session principale, après validation humaine des findings à intégrer,
  en commits `feat:` (réécriture fidèle) puis `fix:` (corrections validées), avant que les goldens soient figés ;
- la preuve de fidélité au pixel entre l'export et la réécriture : voir le rapport de la phase 1,
  qui propose la méthode.

### 4.3 Décisions après la phase 1 (2026-09-18)

La revue est dans `docs/review.md`. Décisions humaines :

- **Ordre** : outillage, puis réécriture prouvée fidèle, puis corrections, puis goldens. La phase 2 est
  coupée en trois :
  - **2a, agent `quality-gates`** : tout l'outillage du §6 sauf le scénario complet et les goldens
    (justfile, treefmt, ruff, prettier, Dockerfile pinné, requirements + lock, scripts `test/ci/`,
    `golden.py`, `test/site/run-tests.sh` et des tests pytest qui passent sur le repo tel qu'il est).
    `just lint` vert à la fin ;
  - **2b, session principale** : `site/vendor/` ; réécriture statique fidèle en un commit `feat:`,
    prouvée par la méthode du §6 de la revue (export servi hors ligne via `page.route`, comparaison au
    pixel près, octets des SVG exportés, pages PDF, textes des 7 langues) ; puis un commit `fix:` par
    correction validée ci-dessous ;
  - **2c, agent `quality-gates`** : scénario e2e sur tous les états de l'annexe B, goldens desktop,
    `just gui-goldens-stability site 3`, workflow `.github/workflows/ci.yml`.
- **Corrections à faire avant les goldens** : les 10 points du §4 de la revue, plus :
  - **B3** : le lien « Code source » pointe vers `https://github.com/CestMoiRoma/Printed-Labels-maker` ;
  - **I6** : palette AA, tout texte porteur d'information en `#b0a79e` ou `#8a827a` passe en `#6b645d` ;
  - **B4** : bornes du tableau de la revue, telles que proposées.
- **Corrections avant déploiement** : le §5 de la revue, traité en phase 5 (ou plus tôt si c'est gratuit
  pendant la réécriture, sans changer le rendu prouvé par le commit `feat:`).

## 5. Phase 1 : agent `reviewer` (code + design)

Mission : produire `docs/review.md`. Ne modifie aucun fichier du site.

**Revue du code**

- HTML sémantique (landmarks, headings, labels liés aux champs, boutons vs liens).
- CSS : dead code, valeurs magiques qui devraient venir des tokens du JSON, spécificité, responsive.
- JS : erreurs console, dépendances externes (CDN) qui ne passeront pas en prod sans CSP ou hors ligne,
  état non géré (formulaire vide, valeur invalide, taille d'étiquette hors gamme), impression
  (`@media print`, marges, unités physiques mm / pouces cohérentes avec le format d'étiquette).
- Compatibilité Workers : pas d'URL absolue codée en dur, pas de chemin dépendant d'un serveur applicatif.
- Accessibilité : contraste, focus visible, navigation clavier sur tout le flux, textes alternatifs.
  **Revue du design**

- Fidélité au JSON de Claude Design : chaque token (couleurs, espacements, typo, rayons) utilisé dans le
  CSS doit correspondre à une valeur du JSON. Lister les écarts avec fichier : ligne.
- Cohérence entre états (vide, rempli, aperçu, erreur, impression) et entre viewports.
- Ce qui manque dans l'export : états d'erreur, état vide, hover / focus, mobile.
  **Format du rapport**

Findings triés par sévérité (bloquant / important / mineur), chacun avec fichier : ligne, constat,
correction proposée. Une section finale « à corriger avant de figer les goldens » et une section
« à corriger avant le déploiement ». Pas de généralités : chaque point est vérifiable.

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

## 7. Phase 3 : agent `cloudflare` (Workers)

Mission : rendre le site déployable sur Cloudflare Workers avec les assets statiques, sans worker
applicatif tant qu'aucune logique serveur n'est nécessaire.

**Livrables**

- `wrangler.jsonc` : `name`, `compatibility_date` figée à la date du jour, bloc `assets` pointant sur le
  dossier servi (`site/` ou `dist/`), `not_found_handling` adapté (page 404 dédiée ou `404-page`).
  Vérifier la syntaxe courante dans la doc Workers Static Assets avant d'écrire : ce format bouge.
- Worker minimal (`src/worker.js`) **uniquement** si le site a besoin de headers custom, de redirections
  ou d'une route dynamique. Sinon, aucun script ; les headers de sécurité et de cache passent par les
  mécanismes statiques supportés (fichiers `_headers` / `_redirects` si disponibles pour les assets Workers).
- `package.json` avec `wrangler` en devDependency épinglée, `package-lock.json` commité et exclu de treefmt.
- `.gitignore` : `.wrangler/`, `.dev.vars`, `node_modules/`.
- Recettes `just dev` (`wrangler dev`) et `just deploy` (`wrangler deploy`), natives sur l'hôte : le build
  et le déploiement sont l'exception autorisée par le playbook.
- Vérification hors ligne intégrée aux tests : `wrangler deploy --dry-run --outdir /tmp/wrangler-out`
  dans `run-tests.sh` mode `tests`, pour que la config soit validée à chaque `just ci`.
  Wrangler est alors épinglé dans l'image CI (base `node:22`, install par `npm ci` dans une copie sous `/tmp`).
- Job `deploy` en CI : déclenché sur la branche principale seulement, après `goldens:site`, avec
  `cloudflare/wrangler-action` épinglé par SHA, secrets `CLOUDFLARE_API_TOKEN` et `CLOUDFLARE_ACCOUNT_ID`.
  Documenter dans le rapport comment créer le token (scope Workers Scripts : Edit).

**Contrainte**

Le dossier servi par wrangler est le même que celui parcouru par le scénario e2e. Si l'agent introduit
un build, il met à jour `run-tests.sh` et prévient : ce n'est pas son périmètre, mais la phase 2 doit rester vraie.

## 8. Phase 4 : agent `readme`

Mission : écrire `README.md`. C'est le texte qu'un dev écrit pour un autre dev, pas une plaquette.

**Contenu, dans cet ordre**

1. Ce que fait le site, en deux ou trois phrases.
2. Une capture : réutiliser un golden (`test/screenshot/site/01-home.png`), pas une image à part.
3. Lancer en local : `just dev`.
4. Vérifier : `just lint`, `just test site`, `just ci`, et le workflow goldens en trois lignes.
5. Déployer : `just deploy`, les deux secrets, et le fait que la CI déploie depuis la branche principale.
6. Arborescence, en quelques lignes seulement.
7. Licence.

**Style, à respecter à la lettre**

- Aucun tiret cadratin (`—`) ni demi-cadratin (`–`) dans tout le fichier. Pour couper une phrase :
  une virgule, deux points, un point, ou deux phrases.
- Pas d'emoji, pas de badges, pas de « 🚀 », pas de « Bienvenue ».
- Pas de titres en kit (« Features », « Getting Started », « Contributing », « Roadmap »). Des titres qui
  disent ce qu'il y a dessous.
- Pas d'adjectifs de remplissage (robuste, puissant, moderne, seamless, comprehensive, leverage),
  pas de « ce projet vise à », pas de listes de trois pour le rythme, pas de gras sur chaque mot clé.
- Des phrases courtes, à la voix active, qui disent une chose. Une liste seulement quand c'est une
  vraie liste (commandes, fichiers). Le reste en paragraphes.
- Pas de section vide ni de placeholder. Ce qui n'existe pas n'est pas mentionné.
- Test avant de rendre la main : `grep -n '[—–]' README.md` doit ne rien retourner, et le fichier se lit
  à voix haute sans qu'on entende un modèle.

Facultatif mais recommandé : ajouter `test/ci/check_prose.py` comme linter treefmt sur `*.md`, qui échoue
sur tout tiret cadratin ou demi-cadratin. Le style devient alors une gate comme les autres.

## 9. Phase 5 : intégration finale (session principale)

1. Corriger ce que le reviewer a marqué « avant déploiement », en commits `fix:` séparés.
2. Si un fix touche le rendu : `just site-gui-goldens`, revue des images, commit avec la liste des captures.
3. `just gui-goldens-stability site 3` puis `just ci` : tout vert, sinon on corrige la cause.
4. `CLAUDE.md` : coller le snippet du §9 du playbook avec les noms adaptés (`site`), plus deux lignes sur
   Cloudflare (`just dev`, `just deploy`, ne jamais déployer avec une CI rouge) et une ligne sur le style
   du README (pas de tiret cadratin).
5. Rapport final : liste des commits, points ouverts restants, commandes de vérification.

## 10. Points à trancher avant de lancer

| Point                              | Valeur                                                                                                                                                                                                                       | État                  |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| Fichiers exportés de Claude Design | `design/label-generator.dc.html` et `design/support.js` ; pas de JSON (§4.1)                                                                                                                                                 | décidé : pas de JSON  |
| Dossier cible du site              | `site/` (réécriture statique), servi tel quel                                                                                                                                                                                | décidé                |
| Découpage du HTML                  | réécriture statique `index.html` / `styles.css` / `app.js` + `site/vendor/` (§4.2)                                                                                                                                           | décidé                |
| Forge                              | GitHub Actions (`.github/workflows/ci.yml`), le remote est sur GitHub                                                                                                                                                        | constaté              |
| Langue du README                   | anglais : le README actuel tient en un titre, le repo est public sur GitHub                                                                                                                                                  | proposé               |
| Viewports des goldens              | `1280×820` seul ; `390×844` ajouté avec la future mise en page mobile                                                                                                                                                        | décidé                |
| Cloudflare : nom du worker         | celui créé côté Cloudflare ; `name` de `wrangler.jsonc` doit lui être identique                                                                                                                                              | à fournir             |
| Cloudflare : déploiement           | worker relié au repo GitHub par l'intégration Git de Cloudflare (Workers Builds), en cours côté humain. À réconcilier en phase 3 avec le job `deploy` du §7 et la règle « jamais de déploiement avec une CI rouge »          | à trancher en phase 3 |
| Cloudflare : domaine               | `printed-labels.roma.moonmakers.fr`, en Custom Domain du worker (`routes` avec `custom_domain: true` dans `wrangler.jsonc`, syntaxe à vérifier dans la doc). La zone `moonmakers.fr` doit être sur le même compte Cloudflare | décidé                |
| Cloudflare : compte cible          | fourni par les secrets `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN`                                                                                                                                                      | à fournir             |
| Build                              | aucun : `site/` est déployé tel quel                                                                                                                                                                                         | proposé               |

## 11. Prompt de démarrage

À coller dans Claude Code une fois les points du §10 renseignés dans ce fichier :

```
Lis PLAN.md et docs/quality-gates.md en entier avant toute action. Exécute les phases dans l'ordre,
en commençant par la phase 0. Chaque agent est défini dans .claude/agents/ avec la mission copiée
depuis PLAN.md. Le reviewer ne modifie rien. Aucun test ni screenshot ne tourne hors de l'image
test/ci/Dockerfile. Ne passe pas à la phase suivante sans me montrer le rapport de la phase en cours.
Termine par `just ci` vert et le rapport final du §9.
```
