---
name: cloudflare
description: Makes the site deployable on Cloudflare Workers static assets: wrangler config, dev/deploy recipes, offline dry-run check, CI deploy job.
tools: Read, Grep, Glob, Bash, Edit, Write, WebFetch
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

Périmètre d'écriture : `wrangler.jsonc`, `package.json`, `package-lock.json`, `.gitignore`,
`site/_headers` et `site/_redirects` si retenus, `src/worker.js` seulement si justifié, les recettes
`dev` / `deploy` du `justfile`, le job `deploy` de `.github/workflows/ci.yml`, et l'étape dry-run de
`test/site/run-tests.sh` (à signaler dans le rapport, ce fichier appartient à la phase 2).
`WebFetch` sert à vérifier la syntaxe courante dans la doc Workers Static Assets.

Mission, copiée depuis `PLAN.md` :

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
