# Revue de l'export Claude Design (phase 1)

Revue statique de `design/label-generator.dc.html` (1008 lignes) et de `design/support.js` (1911 lignes),
faite le 2026-09-18. Aucun navigateur ni serveur n'a tourné : ce qui ne se prouve qu'à l'exécution est
marqué « à vérifier par le scénario e2e (phase 2) ».

| Fichier | SHA-256 (vérifié, identique au §4.1 de `PLAN.md`) |
|---|---|
| `design/label-generator.dc.html` | `ac741acabb9e679ee740c5a07a4e5fd3155eb31106118e55179e493b5c958be6` |
| `design/support.js` | `8fe7df74405f3c55f49b7249c74ea1397e65d07dea2b1bd3b4a489bec2e28cbe` |

Cette revue est le cahier des charges de la réécriture statique (`PLAN.md` §4.2). Chaque finding indique :

- **Sévérité** : bloquant (empêche de déployer ou casse la sortie imprimée), important (défaut visible,
  accessibilité, perte de données), mineur (cohérence, dette, cas limite).
- **Où** : `fichier:ligne` (`html` = `design/label-generator.dc.html`, `support.js` = `design/support.js`).
- **Réécriture** : « naturel » si la réécriture statique le corrige sans rien décider (ex. CDN) ;
  « décision » si le correctif change le rendu, le comportement ou les textes et doit être validé par l'humain
  (commit `fix:` séparé, après le commit `feat:` de réécriture fidèle).
- **Goldens** : si le correctif change des pixels ou ajoute un état à capturer.

Il n'y a pas de JSON de design (§4.1) : la revue « fidélité au JSON » est remplacée par une revue de cohérence
interne des tokens (finding M17 et annexe A).

---

## 0. Faits de la phase 0 : vérification

| Fait annoncé | Verdict | Preuve |
|---|---|---|
| Aucune media query d'écran, barre latérale fixe 340 px | Confirmé | seules media queries : `html:21` et `support.js:119`, toutes deux `print` ; `html:29` `width:340px; flex:0 0 340px` |
| Tout vient de CDN | Confirmé | React/ReactDOM/Babel unpkg `support.js:1143-1148` ; qrcode-svg `html:14` ; Google Fonts `html:12-13` et `html:561` ; `@mdi/js` `html:829` ; Material Symbols `html:843` |
| 24 familles de polices chargées à la demande | Confirmé | `html:369` (24 entrées), `loadFont` `html:556-568` |
| Lien « Code source » vers https://google.com | Confirmé | `html:323` |
| `@page` du helmet contre `@page { margin: 0.5cm }` du runtime | Confirmé, et résolu en faveur du helmet | `BASE_CSS` est inséré en tête du `<head>` (`support.js:1851-1853`, `prepend`), le `<style>` du helmet est ajouté à la fin au rendu (`support.js:1476-1483`). Même spécificité, l'ordre gagne : marge effective `0`, `size: A4` (`html:16`). Fragile, voir I13 |
| `new Function` impose `'unsafe-eval'` | Confirmé | `support.js:842-851` (logique du composant) ; `support.js:1218` (x-import, non utilisé ici) |
| Langue via `navigator.language` | Confirmé, précisé | `html:518-522` : `navigator.languages[0]`, puis `navigator.language`, puis `"fr"` ; code inconnu → `"en"` |
| Démo FR datée « 09/2026 », autres langues sans date ? | **Infirmé en partie** | les lignes FR portent `date: "09/2026"` (`html:537-539`). Les tuples `demo` des 7 langues n'ont que 4 champs (`html:393`…`507`), mais `seedDemo` fusionne par-dessus la ligne existante (`html:764`, `Object.assign({}, s.rows[i], …)`) : la date « 09/2026 » est **conservée** dans toutes les langues |
| Champs sans label associé | Confirmé | voir I7 |
| Boutons icône seule (⧉ ×) avec `title` seulement | Confirmé | `html:91-92`, voir M3 |
| Onglets sans sémantique ARIA | Confirmé | `html:109-113`, `html:346-349`, voir M4 |
| Menu de langue sans clavier / Échap | Confirmé | `html:38-73`, `html:767`, voir M5 |
| `hasIcon` basé sur `!!act.iD` : l'image importée n'apparaît pas dans l'aperçu latéral | Confirmé | `html:978` contre `html:588`, voir M1 |
| Export PNG / image importée / polices non embarquées | Confirmé pour les polices ; image importée à vérifier | voir I4, I5 |
| Tailles hors gamme et champs numériques vides (`""`) | Confirmé, avec crash | voir B4 |
| Échecs de chargement des icônes Material avalés | Confirmé | `html:843-851`, voir I10 |
| Bruit `console.info` du runtime | **Non reproduit statiquement** | les deux seuls `console.info` (`support.js:1198`, `support.js:1231`) sont dans le chargeur `x-import`, que ce document n'utilise pas (aucune balise `<x-import>` dans `html`). Le build React est `production.min` : pas d'avertissement de dev. Si du bruit a été observé, il vient d'ailleurs (erreurs d'attributs SVG, voir B4) : à vérifier par le scénario e2e |

---

## 1. Findings bloquants

### B1 · Tout le rendu dépend de CDN tiers

- **Où** : `support.js:1143-1148` (React 18.3.1, ReactDOM, Babel sur unpkg), `support.js:1906-1910` (échec →
  `console.error` et page vide), `html:12-14` (Google Fonts, qrcode-svg), `html:561` (police d'étiquette),
  `html:829` (`import()` de `@mdi/js`), `html:843` (un `fetch` par icône Material).
- **Constat** : hors ligne, derrière un proxy, ou avec une CSP `default-src 'self'`, React ne se charge pas et
  la page reste blanche (le template brut est masqué par `support.js:1818-1822`). Les polices arrivent en
  `display=swap` (FOUT), le QR et les icônes disparaissent sans message. Les goldens ne peuvent pas être
  déterministes avec un réseau en jeu.
- **Correction** : réécriture sans runtime ; tout dans `site/vendor/` : qrcode-svg 1.1.0, un sous-ensemble mdi,
  les 135 SVG Material de la liste `MAT` (`html:370`), les woff2 avec un CSS `@font-face` local.
- **Réécriture** : naturel. **Goldens** : prérequis (déterminisme).

### B2 · La logique est évaluée par `new Function`

- **Où** : `support.js:842-851`.
- **Constat** : la CSP de production devrait autoriser `'unsafe-eval'` pour que la page démarre.
- **Correction** : `site/app.js` chargé par `<script src>`, aucune évaluation dynamique. CSP cible (phase 3) :
  `default-src 'self'; img-src 'self' data: blob:; style-src 'self'; font-src 'self'; script-src 'self'`.
  `img-src data:` reste nécessaire : l'export PNG charge le SVG en `data:` (`html:894`) et l'image importée est
  une data URL (`html:591`). Si la réécriture pose des couleurs dynamiques, passer par `element.style`
  (CSSOM, autorisé sans `'unsafe-inline'`) et non par des attributs `style=` dans du HTML injecté.
- **Réécriture** : naturel. **Goldens** : non.

### B3 · Le lien « Code source » pointe vers google.com

- **Où** : `html:323`.
- **Constat** : lien de placeholder, visible dans les 7 langues (`html:373`).
- **Correction** : pointer vers le dépôt public (remote actuel `git@github.com:CestMoiRoma/Printed-Labels-maker.git`,
  soit `https://github.com/CestMoiRoma/Printed-Labels-maker`), URL à confirmer par l'humain.
- **Réécriture** : décision (URL). **Goldens** : non (seul `href` change).

### B4 · Champs numériques sans bornes : erreurs console, gel, crash

- **Où** : `html:749-754` (`setField` garde `""` tel quel, `NaN` → 0), `html:710-715` (`grid()`),
  `html:705` (`items()` en mode « single »), `html:697-698` (`labelSVG`), `html:611-612` (`rx`),
  `support.js:1084-1098` (erreur de `renderVals` journalisée puis affichée en bandeau rouge).
- **Constat** (chaque cas se reproduit en effaçant un champ au clavier, sans valeur exotique) :
  - Largeur vidée : `width="mm"` et `viewBox="0 0  50"`. Chromium journalise ces attributs invalides comme
    erreurs console (`Error: <svg> attribute width: Expected length, "mm"`) : le scénario e2e échouerait.
    Idem `br` vidé (`rx=""`) et valeurs négatives (`width="-5mm"`, « A negative value is not valid »).
  - Largeur vide ou 0 et écart 0 : `(210 − 2·mx + 0) / 0` → `cols = Infinity`, `totalW = Infinity·0 = NaN`,
    `translate(NaN,NaN)` dans la planche. En mode « single », `Array.from({ length: Infinity })` lève
    `RangeError: Invalid array length` : bandeau d'erreur rouge du runtime, interface cassée.
  - Largeur vide avec l'écart par défaut (3) : `cols = 65`, `rows = 5` (ou `93` si la hauteur est aussi vide),
    donc jusqu'à 6045 étiquettes par page en mode « single ». Chacune est recalculée (recherche binaire +
    mesure canvas) deux fois par rendu (aperçu `html:990-995` et impression `html:996-1001`) : gel de l'onglet.
  - Nombre d'exemplaires sans maximum (`html:776-779`, `html:707`) : 100 000 exemplaires = 10 000 pages SVG
    dans le DOM.
- **Correction** : séparer le texte saisi de la dernière valeur valide ; calculer toujours sur une valeur bornée ;
  afficher l'erreur sous le champ (`aria-invalid`, `aria-describedby`). Bornes proposées, à valider :

  | Champ | Borne proposée |
  |---|---|
  | `w`, `h` | 10 à 210 − 2·mx (resp. 297 − 2·my) |
  | `pad` | 0 à min(w, h) / 2 − 1 |
  | `bw` | 0 à 5 ; `br` 0 à min(w, h) / 2 ; `divW` 0 à 2 |
  | `titlePt`, `subPt`, `bodyPt` | 4 à 72 |
  | `colW` | 4 à w − 2·pad − 12 (déjà bornée au calcul, `html:619`) ; `gapCol` 0 à 20 |
  | `iconSize`, `iconSizeSolo` | 1 à 100 (voir M10 pour 0) |
  | `mx`, `my` | 0 à 50 ; `gap` 0 à 20 |
  | exemplaires `n` | 1 à 999 |

- **Réécriture** : décision (bornes, textes d'erreur dans les 7 langues). **Goldens** : oui, un état
  « valeur invalide » à capturer.

---

## 2. Findings importants

### I1 · Aucune mise en page mobile

- **Où** : `html:27-29` (flex en ligne, aside `flex:0 0 340px`), `html:327` (main), aucune media query d'écran.
- **Constat** : à 390 px de large, la zone principale dispose de 50 px ; boutons d'export et aperçu inutilisables.
- **Correction** : mise en page empilée sous ~900 px (aside au-dessus, pleine largeur, sans `max-height`).
  Report explicite décidé au §10 : goldens `1280×820` seulement jusqu'à cette mise en page.
- **Réécriture** : décision (reportée). **Goldens** : oui quand elle existera (`-mobile`).

### I2 · « SVG planche » n'exporte que la première page

- **Où** : `html:875` (`this.pages()[0]`).
- **Constat** : au-delà de `per` étiquettes (10 par défaut), l'export perd les pages suivantes sans le dire,
  alors que l'impression (`html:996-1001`) les sort toutes.
- **Correction** : un SVG par page (`planche-a4-1.svg`…) ou un seul SVG multi-pages empilées ; au minimum
  un libellé « page 1 / n ».
- **Réécriture** : décision. **Goldens** : non (téléchargement), mais assertion e2e sur le contenu.

### I3 · Le texte qui déborde n'est pas coupé sur la planche

- **Où** : `html:575-584` (coupure aux espaces seulement), `html:648` et `html:690` (pied `code   date`
  jamais mesuré), `html:666-675` (l'auto-fit ne regarde que la hauteur), `html:725` (`<g>` sans `clipPath`).
- **Constat** : un mot plus long que `tw` (référence produit, URL) ou un pied long dépasse à droite. Dans
  l'aperçu, le `<svg>` racine coupe (`overflow` du SVG inline) ; sur la planche et à l'impression, les
  étiquettes sont des `<g>` d'un même SVG : le texte **s'imprime sur l'étiquette voisine**.
- **Correction** : `clipPath` par étiquette dans `sheetSVG` (rectangle `0,0,W,H`), et prise en compte de la
  largeur de la ligne la plus longue (pied compris) dans `layout()`.
- **Réécriture** : décision (change le rendu des cas limites). **Goldens** : oui si le scénario couvre un
  contenu long (recommandé).

### I4 · Les exports SVG et PNG n'embarquent pas les polices

- **Où** : `html:683` (`font-family="Archivo, sans-serif"`), `html:697-698`, `html:879-894`.
- **Constat** : le SVG téléchargé ne s'affiche avec la bonne police que si elle est installée chez le
  destinataire (logiciel de découpe, Inkscape…). Le PNG passe par `<img src="data:image/svg+xml">` : une image
  SVG n'a pas accès aux polices web du document, le texte retombe sur une police système alors que la
  coupure des lignes a été calculée avec la police web (`html:570-574`). Résultat : débordements ou lignes
  mal réparties dans le PNG.
- **Correction** : injecter dans le SVG exporté un `<style>@font-face{src:url(data:font/woff2;base64,…)}</style>`
  limité aux graisses utilisées (les woff2 sont vendorisés, donc disponibles) ; ou convertir le texte en chemins.
  Coût : quelques dizaines de ko par export.
- **Réécriture** : décision (poids des fichiers contre fidélité). **Goldens** : non ; assertion e2e possible
  (le SVG exporté contient `@font-face`).

### I5 · Export PNG sans gestion d'erreur

- **Où** : `html:876-895`.
- **Constat** :
  - pas de `img.onerror` : si le SVG est invalide (voir B4), le clic ne fait rien, sans message ;
  - `c.toBlob(b => URL.createObjectURL(b))` sans test de `b` : au-delà des limites de canvas du navigateur
    (dans Chromium, 32 767 px de côté ou ~268 Mpx de surface, soit une étiquette carrée d'environ 1,4 m à
    300 dpi), `b` vaut `null` et `createObjectURL(null)` lève un `TypeError` non capturé (erreur console) ;
  - `fillRect` avec la couleur de fond sur tout le canvas (`html:885`) : les coins hors de l'arrondi `rx` sont
    remplis, le PNG n'a pas de coins transparents alors que le SVG en a ;
  - image importée : une data URL dans une image SVG est autorisée, le PNG devrait la contenir dans Chromium,
    à vérifier par le scénario e2e (et hors CI sur Safari, qui a longtemps « teinté » le canvas dans ce cas).
- **Correction** : `onerror` et `b === null` → message d'erreur ; bornes de B4 (qui rendent le cas canvas
  impossible) ; coins transparents (ne pas remplir, ou remplir via un chemin arrondi), à décider.
- **Réécriture** : décision (coins) ; le reste naturel. **Goldens** : non.

### I6 · Contrastes de texte insuffisants

- **Où** (ratios WCAG calculés, oklch converti en sRGB) :

  | Couleur de texte | Fond | Ratio | Usages (taille) |
  |---|---|---|---|
  | `#b0a79e` | `#fff` | 2,37 | `countsLine` `html:81` (10 px), version `html:322` (10 px) |
  | `#b0a79e` | `#f7f4f1` | ~2,1 | « A4 — n page(s) » `html:356` (10 px) |
  | `#8a827a` | `#fff` | 3,78 | titres de section `html:80`, `175`, `202`, `225`, `253`, `292` (10 px), sous-ligne des étiquettes `html:88` (9 px), format d'import `html:102` (9 px), `html:142` (9 px), `fillLine` `html:300` (11 px), `qrNote` `html:281` |
  | `#8a827a` | `oklch(0.98 0.012 300)` | 3,56 | `selHint` `html:122` (10,5 px), `#n` `html:120` |
  | `#8a827a` | `oklch(0.97 0.03 300)` | 3,42 | sous-ligne de l'étiquette sélectionnée `html:88` |
  | `#8a827a` | `#f7f4f1` | 3,45 | `editLine` `html:340`, « Taille réelle » `html:345` |

  Tous ces textes font moins de 18,66 px gras : le seuil AA est 4,5:1. Les autres couples passent
  (`#6b645d` sur `#fff` 5,82 ; sur `#f2eeea` 5,05 ; accent `oklch(0.52 0.14 300)` sur blanc 5,85 ; blanc sur
  accent 5,85).
- **Correction** : `#b0a79e` → `#6b645d` (ou un nouveau `#7a736c`, ≈ 4,6:1 sur blanc, à vérifier) ;
  `#8a827a` → `#6b645d` pour tout texte porteur d'information.
- **Réécriture** : décision (palette). **Goldens** : oui, à trancher **avant** de figer.

### I7 · Champs de saisie sans label

- **Où** : `html:123-131` (titre, sous-titre, contenu, code, date, texte du QR : `placeholder` seulement),
  `html:155` (recherche d'icône), `html:103` (liste collée), `html:90` (exemplaires : `title` seulement).
- **Constat** : le placeholder disparaît à la saisie et n'est pas un nom accessible fiable ; les six champs du
  contenu n'ont aucun libellé visible une fois remplis (on ne distingue plus « code » de « date »).
- **Correction** : `aria-label` reprenant le texte du placeholder (sans impact pixel), ou libellés visibles
  comme dans les onglets Style et Impression (`html:177-191`), ce qui change la mise en page.
- **Réécriture** : naturel pour `aria-label` ; décision pour des libellés visibles. **Goldens** : seulement
  si libellés visibles.

### I8 · L'import d'image est inaccessible au clavier

- **Où** : `html:149-150` (`<label>` cliquable, `<input type="file" style="display:none">`).
- **Constat** : `display:none` retire le champ de l'ordre de tabulation ; le `<label>` n'est pas focusable.
  Le flux clavier ne peut pas atteindre l'import.
- **Correction** : champ masqué visuellement (classe `visually-hidden`, pas `display:none`) avec
  `:focus-visible` reporté sur le label ; aucun pixel ne change hors focus.
- **Réécriture** : naturel. **Goldens** : non.

### I9 · Document sans `lang` ni `<title>`

- **Où** : `html:2` (`<html>` nu), `html:3-7` et `html:10-26` (aucun `<title>`), `html:768-772` (le changement de
  langue ne touche pas au document ; `support.js` ne définit jamais `document.title`).
- **Constat** : lecteurs d'écran en mauvaise langue, onglet du navigateur titré par l'URL, césure et
  correcteur orthographique faux.
- **Correction** : `<html lang="fr">` initial, mis à jour avec la langue choisie ; `<title>` = `appTitle` de la
  langue (« Étiquettes de boîtes »), mis à jour aussi.
- **Réécriture** : naturel. **Goldens** : non.

### I10 · Recherche d'icônes : échecs silencieux, ni chargement ni état vide, course entre réponses

- **Où** : `html:828-832` (échec de l'import mdi → liste vide), `html:842-851` (pas de test `r.ok` : une 404
  est parsée, ne donne aucun `<path>`, et l'icône disparaît ; toute exception → `null`), `html:822` et
  `html:823-855` (chaque frappe lance une recherche asynchrone, la plus lente gagne), `html:156-162`
  (grille vide sans message), `html:566` et `html:605` (échec de police et de QR avalés).
- **Constat** : l'utilisateur ne distingue pas « aucun résultat », « chargement » (mdi.js fait plusieurs Mo) et
  « réseau en panne ». Une frappe rapide peut afficher les résultats d'une requête précédente.
- **Correction** : avec les icônes vendorisées, la recherche devient synchrone (plus de course, plus d'échec
  réseau) ; ajouter un état « aucun résultat » dans les 7 langues. Vérifier au vendoring que les 135 noms de
  `MAT` existent (aujourd'hui une 404 est invisible).
- **Réécriture** : naturel (course, réseau) ; décision (texte de l'état vide). **Goldens** : oui, état vide.

### I11 · Changer de langue écrase les modifications de la démo

- **Où** : `html:756-766`.
- **Constat** : `pristine` ne compare que les **titres** aux démos (et l'absence d'icône). Si l'utilisateur
  modifie le sous-titre, le contenu ou le code d'une étiquette de démo sans toucher au titre, puis change de
  langue, ces champs sont remplacés sans avertissement.
- **Correction** : considérer la démo intacte seulement si les quatre champs sont identiques à ceux d'une
  langue (et `date === "09/2026"`).
- **Réécriture** : décision (comportement), simple. **Goldens** : non.

### I12 · Bebas Neue ne peut pas se charger (à vérifier)

- **Où** : `html:369` (Bebas Neue dans la liste), `html:561` (`:wght@400;500;700` pour toutes les familles).
- **Constat** : Bebas Neue n'existe qu'en graisse 400. L'API CSS2 de Google Fonts répond une erreur quand une
  graisse demandée n'existe pas : la police entière n'est pas chargée, l'étiquette s'affiche en police de
  repli. À vérifier au moment du vendoring. Les 23 autres familles couvrent 400, 500 et 700.
- **Correction** : vendoriser les graisses réelles de chaque famille ; pour Bebas Neue, 400 seul (gras
  synthétique ou graisse 400 pour le titre, à décider).
- **Réécriture** : naturel (vendoring) + décision (rendu du gras). **Goldens** : non (police par défaut Archivo).

### I13 · Impression : règles fragiles et marges matérielles

- **Où** : `html:16` (`@page { size: A4; margin: 0 }`), `support.js:119-130` (`@page { margin: 0.5cm }` et
  `print-color-adjust: exact` sur `*`), `html:17` (fond `#f7f4f1` du `body`), `html:998-999`
  (`210mm × 297mm`, `break-after: page` y compris sur la dernière feuille), `html:727-728` (traits de coupe de
  0 à 4 mm des bords).
- **Constat** :
  - la marge effective 0 ne tient qu'à l'ordre d'insertion des `<style>` (voir §0) ; avec la marge 0,5 cm, une
    feuille de 297 mm ne tiendrait plus sur une page et chaque planche en ferait deux ;
  - avec `print-color-adjust: exact`, le fond beige du `body` s'imprimerait sur toute zone non couverte par une
    feuille (arrondi sub-millimétrique, page blanche finale) ;
  - la plupart des imprimantes de bureau ne marquent rien dans les 3 à 5 mm du bord : les traits de coupe
    (0–4 mm et 293–297 mm, 206–210 mm) sont en grande partie perdus, et un pilote en mode « ajuster à la page »
    réduit l'échelle, ce qui fausse les dimensions des étiquettes ;
  - A4 seulement alors que l'anglais est présenté « English (US) » (voir M14).
- **Correction** : un seul `@page { size: A4; margin: 0 }` ; `@media print { body { background: #fff } }` ;
  `print-color-adjust: exact` limité aux feuilles ; pas de `break-after` sur la dernière feuille ; traits de
  coupe arrêtés à la marge de la planche (`ox`/`oy`) plutôt qu'au bord, à décider ; mention « imprimer à 100 %,
  sans mise à l'échelle » près du bouton Imprimer. À vérifier par le scénario e2e : `page.pdf()` doit
  produire exactement `pages().length` pages.
- **Réécriture** : naturel (règles CSS) ; décision (traits de coupe, mention). **Goldens** : capture
  `emulate_media(print)` à faire après ces choix.

### I14 · Étiquette ou marges plus grandes que la feuille : aucun avertissement

- **Où** : `html:710-715`, `html:719`.
- **Constat** : avec des valeurs valides, `w > 210 − 2·mx` donne quand même `cols = 1` (`Math.max(1, …)`) et
  l'étiquette sort de la feuille (coupée par le `viewBox` 210×297). `gridInfo` affiche « 1 × 1 = 1 » comme si
  tout allait bien. Idem pour des marges de 150 mm.
- **Correction** : bornes de B4 liées à la feuille, ou message « l'étiquette ne tient pas sur une feuille A4 ».
- **Réécriture** : décision (avec B4). **Goldens** : oui si un état d'erreur est ajouté.

### I15 · Recalcul complet de toutes les étiquettes à chaque frappe

- **Où** : `html:900-1003` (`renderVals` reconstruit tout), `html:990-995` et `html:996-1001` (planche d'aperçu
  **et** planches d'impression cachées, donc deux `buildInner` par étiquette), `html:666-675` (jusqu'à 15
  mises en page par étiquette, chacune mesurant chaque mot au canvas).
- **Constat** : avec 200 étiquettes, chaque caractère tapé déclenche ~400 × 15 mises en page. Le goulot n'est
  pas visible avec les 3 étiquettes de démo.
- **Correction** : mémoïser le SVG par (ligne, réglages de style) ; ne construire les planches d'impression
  que sur `beforeprint` ; réutiliser la même chaîne SVG pour les copies d'une même ligne.
- **Réécriture** : naturel. **Goldens** : non.

---

## 3. Findings mineurs

### M1 · L'image importée n'apparaît pas dans l'aperçu latéral
`html:978` (`hasIcon: !!act.iD`) et `html:139-141` (seul un `<path>` est prévu) contre `html:588`
(`hasIcon()` qui compte l'import). Seul le nom du fichier s'affiche (`html:983`). Correction : `hasIcon` =
`this.hasIcon(act)` et un `<img src=iUrl>` 20×20 pour l'import. Réécriture : décision (pixels de l'état
« image importée »). Goldens : oui si le scénario importe une image.

### M2 · Le glyphe ⧉ n'existe pas dans Public Sans
`html:91`. U+29C9 est absent de Public Sans et de JetBrains Mono : il est rendu par une police de repli du
système (DejaVu, Noto Sans Math…). Rendu différent d'une machine à l'autre, et golden dépendant des polices de
l'image CI. Correction : icône SVG vendorisée (mdi `content-copy`, 13 px). Réécriture : décision. Goldens :
oui, à trancher avant de figer.

### M3 · Boutons icône seule : noms ambigus
`html:91-92` : le `title` donne un nom accessible (« Dupliquer », « Supprimer »), mais identique pour chaque
ligne, et invisible au clavier et au toucher. Correction : `aria-label` avec le titre de la ligne
(« Supprimer Câbles & chargeurs »). Réécriture : naturel. Goldens : non.

### M4 · Onglets et bascules sans sémantique ; sélection signalée par la couleur seule
`html:109-113` et `html:346-349` sont des `<nav>` (landmarks de navigation) alors que ce sont des onglets
(`role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`) ; deux `<nav>` sans `aria-label`.
La ligne sélectionnée (`html:86`, `html:975-976`) et la langue courante (`html:917`) n'ont ni `aria-pressed`
ni `aria-current`. Réécriture : naturel. Goldens : non.

### M5 · Menu de langue : ni Échap, ni clic extérieur, ni ARIA
`html:38`, `html:54-73`, `html:767-772`. Le menu ne se ferme qu'en choisissant une langue ou en recliquant le
bouton ; pas d'`aria-expanded`, `aria-haspopup`, ni de nom explicite (le bouton se lit « FR »). Correction :
Échap et clic extérieur ferment et rendent le focus au bouton ; `aria-expanded` ; `aria-label` « Langue :
Français ». Réécriture : naturel. Goldens : non.

### M6 · Une seule balise de titre
Seul `html:34` est un `<h1>` ; les titres de section (`html:80`, `119`, `175`, `202`, `225`, `253`, `292`,
`345`) sont des `<div>`. Correction : `<h2>` avec les mêmes styles (reset `margin`, `font-weight` explicite).
Réécriture : naturel si le style est remis à l'identique. Goldens : non.

### M7 · Contraste des bordures de champ
`#ddd6ce` sur `#fff` : 1,44:1 (49 occurrences, `html:90`, `123`, …) ; `#e6e1db` 1,30:1 (lignes non
sélectionnées `html:976`) ; `#c9c1b8` 1,74:1 (`html:97`). WCAG 1.4.11 demande 3:1 pour la limite d'un
contrôle. Réécriture : décision (palette). Goldens : oui.

### M8 · Le centrage vertical est calculé avec d'autres interlignes que le rendu
`html:659-662` estime la hauteur avec 1,2 (titre), 1,25 (sous-titre), 1,32 (liste) et `fS·1,1` (pied) ;
`put()` (`html:681-685`) avance toujours de `0,88 + 0,32 = 1,2 × taille`. La hauteur estimée dépasse la
hauteur réelle : le bloc est trop haut (non centré) et l'auto-fit laisse du vide. À reproduire à
l'identique pour la réécriture fidèle ; correction (mêmes coefficients des deux côtés) en `fix:`.
Réécriture : décision. Goldens : oui.

### M9 · Les espaces volontaires disparaissent
Pied : `[code, date].join("   ")` (`html:648`) ; liste en ligne : `join("  ·  ")` (`html:656`). `wrap()`
recoupe aux espaces et recolle avec un seul (`html:576-583`) et le SVG replie les blancs (pas de
`xml:space`). Rendu réel : « B-014 09/2026 » et « USB-C, · HDMI » avec possible retour à la ligne juste
avant ou après « · ». Correction : `<tspan dx>` pour l'écart du pied ; coupure qui garde « · » attaché.
Réécriture : décision. Goldens : oui.

### M10 · Une taille 0 vaut « maximum »
`html:632` et `html:637` (`+s.iconSize || 99`, `+s.iconSizeSolo || 99`), `html:619` (`+s.colW || 20`) : les
champs acceptent `min="0"` (`html:256`, `262`, `265`) mais 0 donne la taille maximale. Correction : 0 masque
l'icône, ou borne minimale 1 (B4). Réécriture : décision. Goldens : non.

### M11 · Supprimer une ligne au-dessus de la sélection change d'étiquette sélectionnée
`html:789-796` : `sel` est seulement borné, pas décrémenté quand `i < sel`. Exemple : 4 lignes, `sel = 2`,
suppression de la ligne 0 → la sélection passe de la 3ᵉ étiquette d'origine à la 4ᵉ. Réécriture : décision
(correctif évident). Goldens : non.

### M12 · Le nombre d'exemplaires ne peut pas être vidé
`html:776-779` : `""` devient 1 immédiatement (champ contrôlé), taper « 5 » donne « 15 ». Correction :
tolérer le champ vide pendant la saisie, valider au `change`/`blur`. Réécriture : décision. Goldens : non.

### M13 · Import collé : séparateurs en conflit, colonne cachée, sans confirmation
`html:801` coupe sur `|`, `;` et tabulation, alors que `;` sépare aussi les éléments du contenu
(`html:585`) : un contenu « vis; écrous » décale les colonnes. Une 6ᵉ colonne `qrText` est lue mais absente
du format affiché (`html:377`). « Remplacer la liste » (`html:804`) écrase tout sans confirmation ni
annulation et repasse en mode « batch » sans le dire. Réécriture : décision. Goldens : non.

### M14 · Textes et formats
- « Upload » non traduit en fr, de, it, pt, nl (`html:381`, `438`, `457`, `476`, `495` ; seul es a « Subir »).
- L'anglais est présenté « English (US) » avec drapeau US (`html:511`) mais écrit en anglais britannique
  (« millimetres », « Centred », « colours », `html:394-411`), et la feuille reste A4.
- Le zoom s'affiche avec un point dans toutes les langues (`html:906`, « ×1.59 ») ; la variante à virgule
  `zoomLabel` (`html:989`) n'est jamais utilisée.
- Noms de fichiers en français quelle que soit la langue (`html:874`, `875`, `890`).
- Littéraux non traduits : « QR code » (`html:281`), « PNG 300 dpi » (`html:332`), « MDI », « Material »
  (`html:147-148`) ; acceptable, à confirmer.

Réécriture : décision. Goldens : oui pour « Upload » (visible dans l'onglet Contenu, état par défaut).

### M15 · Langue et état non persistés ; flash de la démo française
`html:518-522` : repli `"fr"` si `navigator` n'a pas de langue mais `"en"` pour un code inconnu ; `html:905`
retombe sur `DICT.fr` et `SOURCE.en`. Le choix de langue et toutes les étiquettes sont perdus au
rechargement (aucun stockage). Pour une langue autre que fr, le premier rendu affiche la démo française puis
`componentDidMount` la remplace (`html:552`). Correction : semer la démo avant le premier rendu ;
`localStorage` pour la langue (et, à décider, pour la liste). Réécriture : naturel (flash) ; décision
(persistance). Goldens : non (locale `fr-FR`).

### M16 · Code et CSS morts
- État et valeurs jamais lus : `repeat` (`html:535`), `perPage` (`html:965`), `rowCount` (`html:969`),
  `totalCount` (`html:970`), `sizeLabel` (`html:984`), `zoomLabel` (`html:989`).
- `a { color }` et `a:hover` (`html:18-19`) sont écrasés par le `style` en ligne du seul lien (`html:323`) :
  le lien n'a en fait aucun état de survol.
- `overflow-y:auto` de `html:338` ne s'active jamais (`main` n'a pas de hauteur bornée).
- `<meta name="omelette-owns-print">` (`html:11`) n'est lu nulle part dans `support.js` (propre à l'hôte
  Claude Design).
- JetBrains Mono 500 est chargé (`html:13`) mais aucun texte d'interface en mono ne demande 500.

Réécriture : naturel (ne pas reproduire). Goldens : non.

### M17 · Tokens : valeurs isolées et quasi-doublons
Détail et comptes en annexe A. À trancher (fusion = pixels) :
- blancs écrits `#fff` (56) et `#ffffff` (8) ;
- sept gris chauds de bordure/fond proches : `#ddd6ce`, `#e0dad3`, `#e6e1db`, `#ece7e1`, `#f0ece7`,
  `#f2eeea`, `#f4f0eb` (dont trois à une seule occurrence) ;
- textes `#3a342f` et `#4a443e` pour le même rôle (boutons secondaires `html:331` contre `html:194`) ;
- accent à quatre luminosités : 0,52 (principal), 0,48 (isolé, `html:119`), 0,45 (onglet actif), 0,42
  (survol mort, voir M16) ;
- teintes d'accent `oklch(0.97 0.03 300)` et `oklch(0.98 0.012 300)` (isolée, `html:117`) ;
- tailles 10,5 px (2) et 11,5 px (6) en demi-pas, 14 px isolé pour « × » à côté de 13 px pour « ⧉ »
  (`html:91-92`) ;
- ombres à trois opacités (0,04 / 0,06 / 0,1).

Réécriture : décision (fusion) ; en réécriture fidèle, reproduire tel quel via des variables CSS nommées.

### M18 · Incohérences de composants
- Champs texte : `padding:8px` dans l'onglet Contenu (`html:123-131`) contre `7px 8px` partout ailleurs
  (`html:155`, `178`…) : deux hauteurs de champ.
- Contrôles segmentés : rayon 9 px (`html:109`) contre 8 px (`html:346`) pour le même composant.
- Aucun état de survol, d'appui ni de désactivation sur les boutons (seul `cursor:pointer`) ; « × » reste
  actif quand il ne reste qu'une ligne (`html:792`, clic sans effet).
- Pas d'indication de la source d'icône active parmi Aucun / MDI / Material / Upload (`html:146-151`) hormis
  le petit texte `html:142`.

Réécriture : décision. Goldens : oui si corrigé.

### M19 · Barre latérale et en-tête non collants
`html:29` (`max-height:100vh` sans `position:sticky`), `html:328`. En vue « Page entière » avec plusieurs
pages, faire défiler emporte la barre latérale et les boutons d'export hors de l'écran. Réécriture :
décision. Goldens : non (capture en haut de page).

### M20 · « Taille réelle » n'est pas la taille réelle
`html:988` et `html:352` : des `mm` CSS (96 px par pouce), donc la taille physique dépend de l'écran.
Correction : libellé « Taille réelle (approx.) » ou calibrage, à décider. Goldens : oui si le libellé change.

### M21 · QR : lisibilité non contrôlée
`html:602` : couleur = encre `fg` (une encre claire sur fond sombre donne un QR inversé, mal lu par beaucoup
de lecteurs) ; aucune alerte quand le module devient trop petit (70×37 : cellule de 12 mm pour un texte
long) ; si la bibliothèque manque, le QR disparaît sans message alors que la case est cochée (`html:600`,
`html:617`). Réécriture : naturel pour la bibliothèque ; décision pour les alertes.

### M22 · Chaînes injectées sans échappement dans du `innerHTML`
`html:595` (`d` de l'icône, venu d'un attribut `data-d` rempli depuis le CDN), `html:593` (`iVB`),
`html:591` (`href` de l'image). Surface XSS si la source d'icônes est compromise. Correction : échapper avec
`esc()` comme le texte (`html:569`). Réécriture : naturel. Goldens : non.

### M23 · Import d'image non contrôlé
`html:860-866` : ni taille maximale ni vérification du type réel ; la data URL est recopiée dans chaque
étiquette de l'aperçu **et** des planches d'impression (`html:591`). Une photo de 10 Mo × 100 exemplaires
sature la mémoire. Correction : limite (ex. 2 Mo), réduction à 600 px, message d'erreur. Réécriture :
décision.

### M24 · `height="auto"` sur le SVG de planche (à vérifier)
`html:732`. Certains Chromium journalisent `Error: <svg> attribute height: Expected length, "auto"` : à
vérifier par le scénario e2e (vue « Page entière »). Correction sans impact pixel : omettre `height`,
`width="100%"` et le `viewBox` suffisent. Réécriture : naturel.

### M25 · Pas de favicon (à vérifier)
`html:3-7`. Une requête `/favicon.ico` en 404 peut apparaître en erreur console. Correction : favicon dans
`site/` ou `<link rel="icon" href="data:,">`. Réécriture : naturel.

### M26 · Marges « minimales » et un seul écart
`html:719` : la grille est centrée, `mx`/`my` ne sont qu'un minimum ; `html:712-713` : un seul `gap` pour les
deux axes. Impossible de caler la grille sur une planche d'étiquettes prédécoupées (pas horizontal et
vertical différents, décalage exact). Réécriture : décision (fonction). Goldens : non tant que c'est inchangé.

### M27 · Le runtime garde les nœuds de blancs contenant une espace
`support.js:572` supprime les nœuds texte blancs sans espace (sauts de ligne seuls) mais garde ceux qui
contiennent l'indentation. La réécriture statique garde tout. Sans effet dans les conteneurs flex et grid ;
à surveiller dans les contextes en ligne (`html:281` « QR code <span> », `html:149` le label d'import).
C'est la comparaison au pixel (§6) qui tranche. Réécriture : naturel.

---

## 4. À corriger avant de figer les goldens

Ordre proposé : commit `feat:` de réécriture fidèle, preuve de fidélité (§6), puis les `fix:` ci-dessous,
puis goldens.

1. **B1** vendoriser polices, QR et icônes : rien du CDN, sinon aucun golden n'est stable.
2. **M2** remplacer ⧉ par une icône SVG (sinon le golden dépend des polices de repli de l'image CI).
3. **I6** et **M7** décider la palette de contraste (touche presque toutes les captures).
4. **B4** et **I14** bornes et état d'erreur des champs numériques (nouvel état à capturer, textes 7 langues).
5. **I10** état « aucun résultat » de la recherche d'icônes (nouvel état).
6. **I3** découpe des étiquettes sur la planche ; **M8** et **M9** centrage et espaces (ou report explicite :
   dans ce cas les goldens figent le comportement actuel et le `fix:` ultérieur les régénère).
7. **M14** « Upload » traduit et virgule décimale du zoom en français (visibles dans l'état par défaut).
8. **M1** image importée dans l'aperçu latéral, si le scénario couvre l'import.
9. **I13** règles d'impression (une seule `@page`, fond blanc, dernière feuille) avant la capture
   `emulate_media(print)`.
10. Déterminisme de la réécriture : attendre `document.fonts.load()` de la police d'étiquette **avant** la
    première mesure (`html:564-567` refait un rendu après coup), sans `display=swap`.

## 5. À corriger avant le déploiement

1. **B1**, **B2** : aucune ressource externe, aucune évaluation dynamique ; CSP stricte (phase 3).
2. **B3** : vraie URL du lien « Code source ».
3. **B4**, **I14** : bornes des champs, plus aucun crash ni gel.
4. **I9** : `lang` et `<title>`.
5. **I7**, **I8** : labels accessibles, import d'image au clavier ; **M3**, **M4**, **M5** (ARIA, sans pixel).
6. **I2** : export de toutes les pages de la planche.
7. **I4**, **I5** : polices embarquées dans les exports, gestion d'erreur du PNG.
8. **I11** : ne plus écraser les modifications au changement de langue.
9. **I13** : mention « imprimer à 100 % » et PDF au bon nombre de pages vérifié en e2e.
10. **I15** : mémoïsation, au moins pour ne pas geler à quelques centaines d'étiquettes.
11. **I1** : mise en page mobile, ou report assumé et noté dans le README (le site est public).
12. **M22**, **M24**, **M25** : échappement, `height="auto"`, favicon.

Compatibilité Workers : rien à signaler côté export au-delà des CDN. Le seul script local est relatif
(`html:6`), aucun chemin ne suppose un serveur applicatif. Le `fetch(location.href)` de rechargement du
template (`support.js:158-164`) disparaît avec le runtime. Les téléchargements passent par des URL `blob:`
créées côté client. La réécriture doit rester en chemins relatifs, compatible avec la racine du Custom Domain
`printed-labels.roma.moonmakers.fr`.

---

## 6. Méthode de preuve de fidélité (export → réécriture)

Demandée par `PLAN.md` §4.2. Elle s'applique au commit `feat:` de réécriture fidèle, avant tout `fix:`.

1. **Faire tourner l'export hors ligne, sans le modifier.** Dans l'image CI, servir `design/` tel quel et
   intercepter le réseau avec `page.route()` : unpkg (React, ReactDOM), jsdelivr (qrcode-svg, `@mdi/js`,
   `@material-symbols/svg-400/outlined/*.svg`), `fonts.googleapis.com/css2?…` (CSS réécrit vers les woff2
   vendorisés) et `fonts.gstatic.com`. Les fichiers servis sont **ceux de `site/vendor/`**. React et ReactDOM
   doivent être les fichiers exacts d'unpkg : le runtime vérifie leur SRI (`support.js:1144`, `support.js:1146`).
   Toute requête non routée fait échouer le test.
2. **Même scénario des deux côtés**, mêmes réglages `golden.py` (`1280×820`, `fr-FR`, horloge fixe), mêmes
   sélecteurs par rôle et texte (les textes sont identiques par construction). Les états : ceux de l'annexe B.
3. **Pixels** : pour chaque état, comparer les deux captures au pixel près
   (`ImageChops.difference(a, b).getbbox() is None`), sans tolérance. Reproduire aussi les enveloppes du
   runtime qui jouent sur la mise en page : `html, body { height: 100%; margin: 0 }` et deux conteneurs
   `height: 100%` (`support.js:132`).
4. **Sorties SVG** : télécharger « SVG (1 étiquette) » et « SVG planche » des deux côtés
   (`page.expect_download()`) et comparer les octets. Les chaînes sont construites par concaténation
   (`html:608-734`) : avec les mêmes polices, elles doivent être identiques caractère pour caractère.
   Le PNG : comparer les pixels décodés.
5. **Impression** : comparer le `innerHTML` des planches `[data-print]` et le nombre de pages de `page.pdf()`.
6. **Textes** : test structurel qui extrait `DICT`, `SOURCE`, `LANGS`, `FONTS`, `MAT` de `html:369-517`
   (évaluation Node dans l'image, qui est basée sur `node:22`) et les compare aux données de `site/`.
   Ce test peut rester en place en permanence ; les étapes 1 à 5 sont un script ponctuel (par exemple
   `test/site/fidelity.py`), lancé au commit `feat:` et cité dans son message. Ensuite, chaque `fix:` change
   des goldens de façon voulue et listée.

---

## Annexe A · Palette et échelles réellement utilisées

Comptes = occurrences dans le template (`html:1-366`) et dans la logique (`html:367-1006`).

### Couleurs d'interface

| Valeur | Template | Logique | Rôle |
|---|---|---|---|
| `#fff` | 53 | 3 | fonds de champs, boutons, cartes |
| `#ffffff` | 1 | 7 | fond de l'aside (`html:29`), onglet actif, planche SVG |
| `#f7f4f1` | 2 | 0 | fond de page (`body`, conteneur écran) |
| `#fdfcfb` | 2 | 0 | fond de l'en-tête, bouton « Ajouter » |
| `#f2eeea` | 2 | 0 | fond des contrôles segmentés |
| `#1b1917` | 31 | 2 | texte principal, encre et bordure d'étiquette par défaut |
| `#3a342f` | 7 | 0 | texte de boutons et d'icônes |
| `#4a443e` | 16 | 0 | texte de boutons secondaires, libellés de cases |
| `#6b645d` | 28 | 5 | texte secondaire, libellés, onglet inactif |
| `#8a827a` | 15 | 0 | titres de section, aides |
| `#b0a79e` | 3 | 0 | compteurs, version, pages |
| `#ddd6ce` | 49 | 0 | bordure standard des contrôles |
| `#e6e1db` | 4 | 2 | bordure de l'aside, de l'en-tête, des cartes ; ligne non sélectionnée |
| `#e0dad3` | 4 | 0 | contour des drapeaux |
| `#f0ece7` | 2 | 0 | séparateurs (`details`, pied de l'aside) |
| `#f4f0eb` | 1 | 0 | séparateur du menu de langue |
| `#ece7e1` | 1 | 0 | bordure des cases d'icône |
| `#c9c1b8` | 1 | 0 | bordure pointillée « Ajouter » |
| `oklch(0.52 0.14 300)` ≈ `#7652ac` | 9 | 1 | accent : kicker, lien, cases, bouton Imprimer, bordure de ligne sélectionnée |
| `oklch(0.48 0.14 300)` ≈ `#6b46a0` | 1 | 0 | kicker « Étiquette sélectionnée » |
| `oklch(0.45 0.14 300)` ≈ `#623e96` | 0 | 5 | texte de l'onglet actif (2 contrôles segmentés) |
| `oklch(0.42 0.14 300)` ≈ `#5a358c` | 1 | 0 | `a:hover` (mort, M16) |
| `oklch(0.97 0.03 300)` ≈ `#f8f1ff` | 0 | 2 | fond de ligne et de langue sélectionnées |
| `oklch(0.98 0.012 300)` ≈ `#f9f7ff` | 1 | 0 | fond de la carte « Étiquette sélectionnée » |
| `oklch(0.92 0.03 300)` ≈ `#e7e1f6` | 2 | 0 | bordure et séparateur de cette carte |
| `rgba(0,0,0,0.04)` / `0.06` / `0.1` | 1 / 0 / 1 | 0 / 1 / 0 | ombres : carte d'aperçu / pages de planche / menu de langue |
| `#111` | 0 | 1 | traits de coupe (SVG, `stroke-width 0.12`) |

Drapeaux (`html:48`, `66`, `510-516`, `916`) : `#0055A4 #FFFFFF #EF4135` (fr, en ligne) ; US : 7 bandes
`#B22234`/`#FFFFFF` et canton `#3C3B6E` 8×7 px ; es `#AA151B #F1BF00 #AA151B` (colonne) ; de `#000000 #DD0000
#FFCE00` (colonne) ; it `#008C45 #F4F5F0 #CD212A` (ligne) ; pt `#006600 #FF0000 #FF0000` (ligne) ; nl
`#AE1C28 #FFFFFF #21468B` (colonne). Cadre 18×12 px, bordure `#e0dad3`, bandes `flex:1 1 0`.

Défauts d'étiquette (`html:529-532`) : bordure `#1b1917`, fond `#ffffff`, encre `#1b1917`.

### Typographie

- Familles : interface `"Public Sans", Helvetica, sans-serif` (`html:17`), 400 / 600 / 700 ;
  `'JetBrains Mono', monospace` (20 occurrences) en 400. Étiquette : famille choisie parmi les 24 de `FONTS`
  (`html:369`, défaut Archivo), graisses 400 / 500 / 700.
- Tailles (106) : 11 px ×37, 13 px ×28, 10 px ×15, 12 px ×13, 11,5 px ×6, 9 px ×3, 10,5 px ×2, 14 px ×1,
  19 px ×1 (`h1`).
- Graisses : 600 ×13, 700 ×2 (`h1`, bouton Imprimer).
- Interlettrage : `0.12em` ×10 (titres mono en capitales), `-0.01em` ×1 (`h1`).
- Interlignes : 1,4 ×2, 1,45 ×2, 1,5 ×2.

### Espacements, rayons, dimensions

- `gap` (72) : 4 px ×26, 8 px ×19, 10 px ×9, 6 px ×5, 22 px ×3, 12 px ×2, 3 px ×2, 5 px ×2, 1 px, 16 px,
  24 px, 28 px ×1.
- `padding` (65) : `7px 8px` ×21, `8px` ×8, `2px` ×4, `5px 9px` ×4, `6px 10px` ×4, `3px` ×3, `8px 4px` ×3,
  `9px 14px` ×3, `6px 12px` ×2, `7px 9px` ×2, puis une fois chacun : `10mm`, `14px`, `16px 24px`,
  `20px 18px 60px`, `22px`, `28px 24px 60px`, `5px 8px`, `6px 4px`, `6px 8px`, `7px`, `9px 16px`.
- `border-radius` (63) : 6 px ×48, 7 px ×4, 999 px ×4, 10 px ×3, 8 px ×2, 5 px ×1, 9 px ×1.
- Bordures (71) : `1px solid #ddd6ce` ×49, `none` ×6, `1px solid #e0dad3` ×4, `1px solid #e6e1db` ×4,
  `1px solid #f0ece7` ×2, et une fois : `1px dashed #c9c1b8`, `#ece7e1`, `#f4f0eb`, accent, `oklch(0.92…)`,
  dynamique `{{ r.bc }}`.
- Dimensions fixes : aside 340 px, menu de langue 160 px, liste d'étiquettes `max-height` 220 px, grille
  d'icônes 150 px, aperçu `max-width` 584 px et `min-height` 200 px, colonne réelle `max-width` 640 px,
  champ d'exemplaires 44 px, boutons icône 26 px, cases 15 px, sélecteurs de couleur hauteur 30 px, icône
  latérale 20 px, drapeaux 18×12 px.
- Grilles : 2 colonnes `1fr 1fr` ; `repeat(auto-fit, minmax(86px|96px|130px, 1fr))` ; icônes
  `repeat(7, 1fr)`.

---

## Annexe B · États de l'interface à reproduire

| Zone | États | Source |
|---|---|---|
| Langue | fermé / ouvert ; langue courante surlignée `oklch(0.97 0.03 300)` | `html:38-73`, `917` |
| Liste d'étiquettes | ligne sélectionnée (fond et bordure accent) / non ; titre vide → « (sans titre) » ; défilement au-delà de 220 px | `html:83-95`, `973-976` |
| Import collé | `details` fermé (défaut) / ouvert | `html:99-106` |
| Onglets | Contenu (défaut) / Style / Impression ; actif fond `#ffffff` texte `oklch(0.45…)`, inactif transparent `#6b645d` | `html:109-113`, `955-963` |
| Contenu | champ « Contenu du QR » visible seulement si QR coché ; source d'icône aucune / MDI / Material / import ; grille de recherche visible pour MDI et Material ; icône affichée à côté de « Logo / picto » si icône à chemin (M1) | `html:130-165` |
| Style | tailles, préréglages 90×50, 70×37, 105×48, 50×50 ; cases séparateurs, auto-fit, QR | `html:171-287` |
| Impression | mode « batch » (défaut) / « single » avec la phrase `fillLine` | `html:289-319` |
| Aperçu d'édition | étiquette seule / avec icône / avec QR / icône + QR ; auto-fit actif ou non | `html:340-341`, `608-693` |
| Taille réelle | « Par étiquette » (défaut) / « Page entière » (liste des pages, masquable par la prop `showSheetPreview`) | `html:343-359`, `990` |
| Impression navigateur | écran masqué, planches `[data-print]` visibles | `html:21-24`, `364` |
| Erreurs | aucun état d'erreur, de chargement ni de résultat vide dans l'export (voir B4, I10) | — |
| Survol / focus | aucun style propre ; anneau de focus natif du navigateur conservé partout (aucun `outline:none`) : la réécriture ne doit pas en ajouter | — |

État initial (`html:528-544`) : `w 90, h 50, pad 5, align left, bw 0.4, br 3, borderColor #1b1917, bg #ffffff,
fg #1b1917, font Archivo, titlePt 15, subPt 9, bodyPt 8, listStyle lines, iconSize 14, iconSizeSolo 26,
colW 20, gapCol 3, divider true, divW 0.3, autoFit true, qr false, mode batch, sel 0, tab content,
realView label, langOpen false, mx 8, my 10, gap 3, cut true`, et trois lignes de démo, 1 exemplaire chacune.
Props (`html:367`) : `startMode` (`batch`), `showSheetPreview` (`true`), `defaultFont` (`Archivo`).

Textes calculés de l'état initial en français : « 3 modèle(s) · 3 au total », « 2 × 5 = 10 étiquettes par
page A4 · 3 au total », « Édition — 90 × 50 mm · zoom ×1.59 », « A4 — 1 page(s) », « #1 », « v1.0.0 »,
source d'icône « aucun ».

---

## Annexe C · Textes par langue

- 7 langues (`html:509-517`, dans cet ordre) : fr « Français », en « English (US) », es « Español »,
  de « Deutsch », it « Italiano », pt « Português », nl « Nederlands ». Le bouton affiche le code en
  capitales.
- `DICT` (`html:374-508`) : 81 clés de texte + `demo` par langue, **mêmes clés dans les 7 langues** (vérifié).
  73 clés sont lues par le template, 8 par la logique (`countsFmt`, `editFmt`, `fillFmt`, `gridFmt`,
  `pagesFmt`, `noTitle`, `srcNone`, `srcFile`, plus `newLabel` via `addRow`). `SOURCE` (`html:373`) donne
  `sourceCode`.
- Gabarits `fmt` (`html:523`) : `{n}`, `{m}`, `{c}`, `{r}`, `{p}`, `{t}`, `{s}`, `{z}` ; une clé absente laisse
  l'accolade telle quelle.
- Démo : 3 tuples (titre, sous-titre, contenu, code) par langue ; la date « 09/2026 » vient des lignes
  françaises et reste dans toutes les langues (§0).
- Littéraux hors dictionnaire : « MDI », « Material », « QR code », « PNG 300 dpi », « 90×50 », « 70×37 »,
  « 105×48 », « 50×50 », « A4 — », « # », « v », « × », « ⧉ ».
- Tirets et symboles présents dans les textes : « — » (U+2014), « · » (U+00B7), « × » (U+00D7), « … » :
  à conserver avec les polices vendorisées (sous-ensemble latin).
- Recommandation : copier `DICT`, `SOURCE`, `LANGS` **tels quels** dans la réécriture et les verrouiller par le
  test structurel du §6, étape 6.

---

## Annexe D · Règles de calcul à reproduire à l'identique

### Grille A4 (`html:710-739`)

- `cols = max(1, floor((210 − 2·mx + gap) / (w + gap)))`, `rows = max(1, floor((297 − 2·my + gap) / (h + gap)))`,
  `per = cols·rows`.
- `totalW = cols·w + (cols − 1)·gap`, `ox = max(mx, (210 − totalW) / 2)` ; idem `oy` avec 297, `rows`, `h`, `my`.
- Étiquette `i` : `x = ox + (i mod cols)·(w + gap)`, `y = oy + floor(i / cols)·(h + gap)`.
- `items()` : mode « batch », chaque ligne répétée `max(1, n)` fois dans l'ordre ; mode « single », `per`
  copies de la ligne sélectionnée. `pages()` : tranches de `per`, jamais vide.
- Planche : `<rect width="210" height="297" fill="#ffffff"/>`, puis un `<g transform="translate(x,y)">` par
  étiquette. Traits de coupe si `cut` : pour chaque étiquette, verticales en `x` et `x + w` de 0 à 4 et de 293
  à 297 ; horizontales en `y` et `y + h` de 0 à 4 et de 206 à 210 ; groupe `stroke="#111" stroke-width="0.12"`
  ajouté après toutes les étiquettes, doublons non fusionnés.
- Dimensions : `width="210mm" height="297mm"` (impression, export) ; `width="100%" height="auto"` (aperçu).
- Valeurs par défaut : 2 × 5 = 10, `ox = 13.5`, `oy = 17.5`.

### Étiquette (`buildInner`, `html:608-693`)

- Cadre : `<rect x=y=bw/2 width=max(0,W−bw) height=max(0,H−bw) rx=br fill=bg>`, `stroke=borderColor
  stroke-width=bw` si `bw > 0`, sinon `stroke="none"`.
- `avail = H − 2·pad`. `qrText = qrText || code || title`. `hasQR = qr && qrText && bibliothèque chargée`.
  Colonne si icône ou QR : `colW = max(4, min(colW || 20, W − 2·pad − 12))`, `gapCol = max(0, gapCol || 0)`.
- Séparateur vertical en `pad + colW + gapCol/2`, de `pad` à `H − pad`, `stroke=fg`, `stroke-width=divW`,
  `opacity 0.55`, si `divider && divW > 0`.
- Icône + QR : séparateur horizontal en `midY = pad + avail/2`, de `pad` à `pad + colW` ;
  `cellH = avail/2 − gapCol/2` ; icône `min(colW, cellH, iconSize || 99)` centrée dans la cellule haute ;
  QR `min(colW, cellH)` centré dans la cellule basse qui commence à `midY + gapCol/2`.
  Icône seule : `min(colW, avail, iconSizeSolo || 99)`, centrée. QR seul : `min(colW, avail)`, centré.
- Texte : `tx = pad + (colonne ? colW + gapCol : 0)`, `tw = max(6, W − pad − tx)`.
- Liste : `splitList` coupe sur `\n`, `,`, `;`, supprime les vides. Mode « lines » : chaque élément préfixé
  `"· "` et coupé séparément ; mode « inline » : `join("  ·  ")` puis une seule coupure.
- Pied : `[code, date].filter(Boolean).join("   ")`, non coupé.
- Tailles (mm) : `PT = 0.352778` ; `tS = titlePt·PT·k`, `sS = subPt·PT·k`, `bS = bodyPt·PT·k`,
  `fS = max(4.5, bodyPt·0.88)·PT·k`.
- Coupure (`wrap`) : mots séparés par des blancs, remplissage glouton, largeur mesurée au canvas avec
  `ctx.font = weight + " " + (taille·10) + 'px "' + police + '", sans-serif'`, largeur / 10.
  Graisses : titre 700, sous-titre 400, liste 400.
- Hauteur estimée : `nTitre·tS·1.2` ; si sous-titre `+ tS·0.35 + nSous·sS·1.25` ; si liste
  `+ max(1, bS·0.9) + nListe·bS·1.32` ; si pied `+ max(1.2, fS·1.1) + fS·1.1`.
- Facteur `k` : auto-fit, dichotomie sur `[0.5, 2.4]`, 14 itérations, on garde `lo` (plus grand `k` qui
  tient, 0,5 au pire) ; sans auto-fit, `k = 1` sauf si ça déborde, alors dichotomie sur `[0.5, 1]`,
  12 itérations.
- Placement : `ty = pad + max(0, (avail − h)/2)` ; chaque ligne : `ty += taille·0.88`, `<text>`, puis
  `ty += taille·0.32`. Avant le sous-titre `ty += tS·0.35`, avant la liste `max(1, bS·0.9)`, avant le pied
  `max(1.2, fS·1.1)`.
- `<text>` : `x` = `tx` (`text-anchor="start"`) ou `tx + tw/2` (`"middle"`) ; `font-family="<police>, sans-serif"`
  (pied : `", monospace"` et `letter-spacing="0.04"`) ; titre 700 sans opacité, sous-titre 400 `opacity 0.72`,
  liste 400 `0.9`, pied 500 `0.65` ; `fill=fg` ; texte échappé par `esc()` (`& < > "`).
- Icône à chemin : `<g transform="translate(x,y) scale(taille / max(vbW, vbH)) translate(−vbX, −vbY)"
  fill=fg><path d/></g>`. Import : `<image x y width height preserveAspectRatio="xMidYMid meet" href=dataURL>`.
- `labelSVG` : `xmlns`, `width="{w}mm" height="{h}mm"` (ou `100%`), `viewBox="0 0 w h"`.

### QR (`html:599-606`)

`new QRCode({ content, padding: 0, width: 100, height: 100, color: fg, background: "transparent", ecl: "M",
join: true, container: "svg-viewbox" })`, balise `<svg>` externe retirée, contenu placé dans
`<g transform="translate(x,y) scale(taille/100)">`. Bibliothèque : qrcode-svg 1.1.0.

### Icônes (`html:823-859`)

- MDI (`@mdi/js` 7.4.47) : exports commençant par `mdi`, nom = reste en kebab-case, `viewBox 0 0 24 24` ;
  filtre `name.includes(q)` en minuscules ; 56 résultats au plus.
- Material (`@material-symbols/svg-400/outlined`) : les 135 noms de `MAT` (`html:370`), filtre
  `includes(q)`, 42 au plus ; `viewBox` du fichier (défaut `0 -960 960 960`) ; tous les `d` joints par une
  espace ; nom affiché avec `_` → espace.
- « Appliquer ce picto à toutes » copie `iSrc, iD, iVB, iUrl, iName` sur toutes les lignes.

### Aperçus (`html:903-906`, `987-988`)

`scale = min(540 / max(1, w), 340 / max(1, h))` ; aperçu `width: min(100%, w·scale px)`,
`aspect-ratio: w / h` ; zoom `"×" + (round(scale / 3.7795 · 100) / 100).toFixed(2)` (défaut « ×1.59 »).
Taille réelle : `width: w mm; height: h mm`, `margin-inline: auto` si `w / 25.4 · 96 ≤ 400`, sinon 0.

### Exports (`html:867-895`)

- SVG : `labelSVG(sélection)` en mm, `etiquette-{w}x{h}mm.svg`, `image/svg+xml`.
- Planche : `sheetSVG(pages()[0], true)`, `planche-a4.svg` (voir I2).
- PNG : `px(mm) = round(mm / 25.4 · 300)` (défaut 1063 × 591), fond `bg` sur tout le canvas, puis le SVG
  dessiné à la taille du canvas ; `etiquette-{w}x{h}mm@300dpi.png`. URL `blob:` révoquée après 3 s.

### Impression (`html:16-24`, `996-1001`)

Une `<div>` par page : `width: 210mm; height: 297mm; overflow: hidden; page-break-after: always;
break-after: page`, contenant `sheetSVG(page, true)`. `@page { size: A4; margin: 0 }`, `[data-screen]` masqué
et `[data-print]` affiché en `@media print`, `print-color-adjust: exact` (runtime, `support.js:124`).

### Comportements des actions (`html:742-896`)

- Ajouter : copie de la ligne sélectionnée (date et icône **conservées**), titre `newLabel`, sous-titre,
  contenu, code, texte QR vidés, `n = 1`, nouvelle ligne sélectionnée.
- Dupliquer : copie insérée juste après, sélectionnée. Supprimer : sans effet s'il reste une ligne.
- Exemplaires : `max(1, parseInt(v) || 1)`.
- Import collé : lignes non vides, champs séparés par `\s*[|;\t]\s*` dans l'ordre titre, sous-titre,
  contenu, code, date, texte QR ; remplace la liste, `sel = 0`, `mode = batch`, vide la zone ; sans effet si
  vide.
- Préréglage : `w`, `h` seulement. Source « Aucun » : efface l'icône et les résultats.
- Changement de police : `loadFont` puis nouveau rendu quand 400 et 700 sont chargés.
- Changement de langue : ferme le menu, ressème la démo si elle est intacte (voir I11).
