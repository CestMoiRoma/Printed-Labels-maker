// Printed Labels Maker: a box label generator (SVG in millimetres, A4 sheets with crop marks).
// Static rewrite of the Claude Design export in design/label-generator.dc.html, without React or CDNs.
// The constants block below is copied byte for byte from the export (test/site/test_texts.py checks it);
// the label geometry (buildInner, sheetSVG, grid, pages) is the export's code, so SVG output is identical.
"use strict";
(() => {
// ---------- constants (from the design export) ----------
const PT = 0.352778;
const FONTS = ["Public Sans","Archivo","Space Grotesk","Work Sans","Libre Franklin","Outfit","Bitter","DM Sans","Manrope","Roboto Mono","JetBrains Mono","Fraunces","Lora","Playfair Display","Oswald","Bebas Neue","Rubik","Nunito Sans","IBM Plex Sans","IBM Plex Mono","Barlow","Cabin","Karla","Sora"];
const MAT = ["home","inventory_2","kitchen","build","bolt","cable","memory","developer_board","hardware","construction","handyman","plumbing","electrical_services","science","biotech","toys","sports_esports","sports_basketball","brush","palette","format_paint","design_services","straighten","architecture","carpenter","key","lock","luggage","backpack","shopping_bag","local_shipping","package_2","archive","folder","description","photo_camera","videocam","headphones","speaker","keyboard","mouse","usb","battery_full","power","lightbulb","flashlight_on","wifi","router","sd_card","save","print","cut","content_paste","label","bookmark","star","favorite","pets","yard","grass","local_florist","park","forest","water_drop","ac_unit","local_fire_department","restaurant","local_cafe","liquor","icecream","cake","egg","set_meal","medication","medical_services","vaccines","cleaning_services","soap","dry_cleaning","checkroom","bed","chair","table_restaurant","door_front","window","stairs","garage","directions_car","two_wheeler","pedal_bike","sailing","flight","train","fitness_center","self_improvement","music_note","piano","mic","radio","tv","computer","smartphone","tablet","watch","calculate","school","menu_book","auto_stories","edit","draw","attach_file","push_pin","link","search","settings","tune","info","warning","recycling","delete","add","remove","check_circle","schedule","calendar_month","numbers","tag","qr_code","apartment","storefront","warehouse","weekend","umbrella","beach_access","hiking"];

const VERSION = "1.0.0";
const SOURCE = { fr: "Code source", en: "Source code", es: "Código fuente", de: "Quellcode", it: "Codice sorgente", pt: "Código-fonte", nl: "Broncode" };
const DICT = {
  fr: { kicker:"Générateur", appTitle:"Étiquettes de boîtes", appSub:"SVG en millimètres, planche A4 avec traits de coupe.",
    labels:"Étiquettes", countsFmt:"{n} modèle(s) · {m} au total", copies:"exemplaires", duplicate:"Dupliquer", remove:"Supprimer",
    addLabel:"+ Ajouter une étiquette", importSummary:"Importer une liste collée", importFormat:"Titre | Sous-titre | contenu, contenu | code | date",
    importPh:"Une ligne par étiquette", importBtn:"Remplacer la liste", tab1:"1 · Contenu", tab2:"2 · Style", tab3:"3 · Impression",
    selected:"Étiquette sélectionnée", selHint:"Titre obligatoire. Laissez un champ vide pour le retirer : la mise en page se recompose et le texte restant occupe la place.",
    phTitle:"Titre (obligatoire)", phSub:"Sous-titre", phContents:"Contenu, séparé par des virgules ou des retours à la ligne", phCode:"Code / n°", phDate:"Date",
    phQr:"Contenu du QR (défaut : le code)", logo:"Logo / picto", none:"Aucun", upload:"Upload", searchPh:"chercher un picto…", applyAll:"Appliquer ce picto à toutes",
    sizeHdr:"Taille de l'étiquette", w:"Largeur mm", h:"Hauteur mm", pad:"Marge intérieure mm", align:"Alignement du texte", left:"Gauche", center:"Centré",
    borderHdr:"Bordure & couleurs", bw:"Épaisseur bordure mm", br:"Arrondi des angles mm", border:"Bordure", bg:"Fond", ink:"Texte & picto",
    typoHdr:"Typographie", font:"Police du texte", titlePt:"Titre pt", subPt:"Sous-titre pt", bodyPt:"Liste pt", listStyle:"Disposition de la liste",
    optLines:"Une ligne par élément", optInline:"Sur la même ligne (· séparateur)",
    colHdr:"Colonne du picto & séparations", colW:"Largeur de colonne mm", gapCol:"Espace avant texte mm", iconSolo:"Picto sans QR mm", iconQR:"Picto avec QR mm",
    divW:"Épaisseur du trait mm", chkDiv:"Afficher les traits de séparation", chkFit:"Adapter la taille du texte à la hauteur", qrNote:"(ajouté sous le picto)",
    printHdr:"Planche A4", modeLbl:"Ce qui est imprimé", modeAll:"Toutes les étiquettes de la liste", modeOne:"Seulement l'étiquette sélectionnée",
    fillFmt:"La page est remplie automatiquement avec l'étiquette sélectionnée ({n} par A4).", mx:"Marge gauche/droite mm", my:"Marge haut/bas mm", gap:"Écart entre étiquettes mm", cut:"Traits de coupe",
    gridFmt:"{c} × {r} = {p} étiquettes par page A4 · {t} au total", btnSvg:"SVG (1 étiquette)", btnSheet:"SVG planche", btnPrint:"Imprimer / PDF A4",
    editFmt:"Édition — {s} · zoom {z}", realHdr:"Taille réelle", byLabel:"Par étiquette", fullPage:"Page entière", pagesFmt:"{n} page(s)",
    noTitle:"(sans titre)", newLabel:"Nouvelle étiquette", srcNone:"aucun", srcFile:"fichier",
    demo:[["Câbles & chargeurs","Bureau — étagère haute","USB-C, HDMI, Jack 3.5","B-014"],["Outils à main","Atelier","Pinces, tournevis, clés","B-015"],["Papeterie","Bureau","Stylos, carnets, post-it","B-016"]] },
  en: { kicker:"Generator", appTitle:"Box labels", appSub:"SVG in millimetres, A4 sheet with crop marks.",
    labels:"Labels", countsFmt:"{n} template(s) · {m} total", copies:"copies", duplicate:"Duplicate", remove:"Delete",
    addLabel:"+ Add a label", importSummary:"Import a pasted list", importFormat:"Title | Subtitle | contents, contents | code | date",
    importPh:"One line per label", importBtn:"Replace the list", tab1:"1 · Content", tab2:"2 · Style", tab3:"3 · Printing",
    selected:"Selected label", selHint:"Title is required. Leave a field empty to drop it: the layout recomposes and the remaining text takes the space.",
    phTitle:"Title (required)", phSub:"Subtitle", phContents:"Contents, separated by commas or line breaks", phCode:"Code / no.", phDate:"Date",
    phQr:"QR content (default: the code)", logo:"Logo / icon", none:"None", upload:"Upload", searchPh:"search an icon…", applyAll:"Apply this icon to all",
    sizeHdr:"Label size", w:"Width mm", h:"Height mm", pad:"Inner margin mm", align:"Text alignment", left:"Left", center:"Centred",
    borderHdr:"Border & colours", bw:"Border width mm", br:"Corner radius mm", border:"Border", bg:"Background", ink:"Text & icon",
    typoHdr:"Typography", font:"Text font", titlePt:"Title pt", subPt:"Subtitle pt", bodyPt:"List pt", listStyle:"List layout",
    optLines:"One line per item", optInline:"On one line (· separator)",
    colHdr:"Icon column & dividers", colW:"Column width mm", gapCol:"Space before text mm", iconSolo:"Icon without QR mm", iconQR:"Icon with QR mm",
    divW:"Divider width mm", chkDiv:"Show divider lines", chkFit:"Fit text size to the height", qrNote:"(added under the icon)",
    printHdr:"A4 sheet", modeLbl:"What gets printed", modeAll:"All labels in the list", modeOne:"Only the selected label",
    fillFmt:"The page is filled automatically with the selected label ({n} per A4).", mx:"Left/right margin mm", my:"Top/bottom margin mm", gap:"Gap between labels mm", cut:"Crop marks",
    gridFmt:"{c} × {r} = {p} labels per A4 page · {t} total", btnSvg:"SVG (1 label)", btnSheet:"SVG sheet", btnPrint:"Print / PDF A4",
    editFmt:"Editing — {s} · zoom {z}", realHdr:"Actual size", byLabel:"Per label", fullPage:"Full page", pagesFmt:"{n} page(s)",
    noTitle:"(untitled)", newLabel:"New label", srcNone:"none", srcFile:"file",
    demo:[["Cables & chargers","Office — top shelf","USB-C, HDMI, 3.5 jack","B-014"],["Hand tools","Workshop","Pliers, screwdrivers, keys","B-015"],["Stationery","Office","Pens, notebooks, sticky notes","B-016"]] },
  es: { kicker:"Generador", appTitle:"Etiquetas de cajas", appSub:"SVG en milímetros, hoja A4 con marcas de corte.",
    labels:"Etiquetas", countsFmt:"{n} plantilla(s) · {m} en total", copies:"copias", duplicate:"Duplicar", remove:"Eliminar",
    addLabel:"+ Añadir una etiqueta", importSummary:"Importar una lista pegada", importFormat:"Título | Subtítulo | contenido, contenido | código | fecha",
    importPh:"Una línea por etiqueta", importBtn:"Reemplazar la lista", tab1:"1 · Contenido", tab2:"2 · Estilo", tab3:"3 · Impresión",
    selected:"Etiqueta seleccionada", selHint:"El título es obligatorio. Deje un campo vacío para quitarlo: la composición se recalcula y el texto restante ocupa el espacio.",
    phTitle:"Título (obligatorio)", phSub:"Subtítulo", phContents:"Contenido, separado por comas o saltos de línea", phCode:"Código / n.º", phDate:"Fecha",
    phQr:"Contenido del QR (por defecto: el código)", logo:"Logo / icono", none:"Ninguno", upload:"Subir", searchPh:"buscar un icono…", applyAll:"Aplicar este icono a todas",
    sizeHdr:"Tamaño de la etiqueta", w:"Ancho mm", h:"Alto mm", pad:"Margen interior mm", align:"Alineación del texto", left:"Izquierda", center:"Centrado",
    borderHdr:"Borde y colores", bw:"Grosor del borde mm", br:"Radio de esquinas mm", border:"Borde", bg:"Fondo", ink:"Texto e icono",
    typoHdr:"Tipografía", font:"Fuente del texto", titlePt:"Título pt", subPt:"Subtítulo pt", bodyPt:"Lista pt", listStyle:"Disposición de la lista",
    optLines:"Una línea por elemento", optInline:"En una línea (· separador)",
    colHdr:"Columna del icono y separadores", colW:"Ancho de columna mm", gapCol:"Espacio antes del texto mm", iconSolo:"Icono sin QR mm", iconQR:"Icono con QR mm",
    divW:"Grosor de la línea mm", chkDiv:"Mostrar líneas de separación", chkFit:"Ajustar el texto a la altura", qrNote:"(añadido bajo el icono)",
    printHdr:"Hoja A4", modeLbl:"Qué se imprime", modeAll:"Todas las etiquetas de la lista", modeOne:"Solo la etiqueta seleccionada",
    fillFmt:"La página se rellena automáticamente con la etiqueta seleccionada ({n} por A4).", mx:"Margen izq./der. mm", my:"Margen sup./inf. mm", gap:"Espacio entre etiquetas mm", cut:"Marcas de corte",
    gridFmt:"{c} × {r} = {p} etiquetas por página A4 · {t} en total", btnSvg:"SVG (1 etiqueta)", btnSheet:"SVG hoja", btnPrint:"Imprimir / PDF A4",
    editFmt:"Edición — {s} · zoom {z}", realHdr:"Tamaño real", byLabel:"Por etiqueta", fullPage:"Página completa", pagesFmt:"{n} página(s)",
    noTitle:"(sin título)", newLabel:"Nueva etiqueta", srcNone:"ninguno", srcFile:"archivo",
    demo:[["Cables y cargadores","Oficina — estante alto","USB-C, HDMI, jack 3.5","B-014"],["Herramientas de mano","Taller","Alicates, destornilladores, llaves","B-015"],["Papelería","Oficina","Bolígrafos, cuadernos, notas","B-016"]] },
  de: { kicker:"Generator", appTitle:"Kistenetiketten", appSub:"SVG in Millimetern, A4-Bogen mit Schnittmarken.",
    labels:"Etiketten", countsFmt:"{n} Vorlage(n) · {m} insgesamt", copies:"Exemplare", duplicate:"Duplizieren", remove:"Löschen",
    addLabel:"+ Etikett hinzufügen", importSummary:"Eingefügte Liste importieren", importFormat:"Titel | Untertitel | Inhalt, Inhalt | Code | Datum",
    importPh:"Eine Zeile pro Etikett", importBtn:"Liste ersetzen", tab1:"1 · Inhalt", tab2:"2 · Stil", tab3:"3 · Druck",
    selected:"Ausgewähltes Etikett", selHint:"Titel ist erforderlich. Ein leeres Feld wird weggelassen: das Layout ordnet sich neu und der restliche Text füllt den Platz.",
    phTitle:"Titel (erforderlich)", phSub:"Untertitel", phContents:"Inhalt, getrennt durch Kommas oder Zeilenumbrüche", phCode:"Code / Nr.", phDate:"Datum",
    phQr:"QR-Inhalt (Standard: der Code)", logo:"Logo / Symbol", none:"Keins", upload:"Upload", searchPh:"Symbol suchen…", applyAll:"Symbol auf alle anwenden",
    sizeHdr:"Etikettengröße", w:"Breite mm", h:"Höhe mm", pad:"Innenrand mm", align:"Textausrichtung", left:"Links", center:"Zentriert",
    borderHdr:"Rahmen & Farben", bw:"Rahmenstärke mm", br:"Eckenradius mm", border:"Rahmen", bg:"Hintergrund", ink:"Text & Symbol",
    typoHdr:"Typografie", font:"Schriftart", titlePt:"Titel pt", subPt:"Untertitel pt", bodyPt:"Liste pt", listStyle:"Listenlayout",
    optLines:"Eine Zeile pro Eintrag", optInline:"In einer Zeile (· Trenner)",
    colHdr:"Symbolspalte & Trennlinien", colW:"Spaltenbreite mm", gapCol:"Abstand vor Text mm", iconSolo:"Symbol ohne QR mm", iconQR:"Symbol mit QR mm",
    divW:"Linienstärke mm", chkDiv:"Trennlinien anzeigen", chkFit:"Textgröße an die Höhe anpassen", qrNote:"(unter dem Symbol)",
    printHdr:"A4-Bogen", modeLbl:"Was gedruckt wird", modeAll:"Alle Etiketten der Liste", modeOne:"Nur das ausgewählte Etikett",
    fillFmt:"Die Seite wird automatisch mit dem ausgewählten Etikett gefüllt ({n} pro A4).", mx:"Rand links/rechts mm", my:"Rand oben/unten mm", gap:"Abstand zwischen Etiketten mm", cut:"Schnittmarken",
    gridFmt:"{c} × {r} = {p} Etiketten pro A4-Seite · {t} insgesamt", btnSvg:"SVG (1 Etikett)", btnSheet:"SVG Bogen", btnPrint:"Drucken / PDF A4",
    editFmt:"Bearbeiten — {s} · Zoom {z}", realHdr:"Originalgröße", byLabel:"Pro Etikett", fullPage:"Ganze Seite", pagesFmt:"{n} Seite(n)",
    noTitle:"(ohne Titel)", newLabel:"Neues Etikett", srcNone:"keins", srcFile:"Datei",
    demo:[["Kabel & Ladegeräte","Büro — oberes Regal","USB-C, HDMI, Klinke 3,5","B-014"],["Handwerkzeug","Werkstatt","Zangen, Schraubendreher, Schlüssel","B-015"],["Schreibwaren","Büro","Stifte, Hefte, Haftnotizen","B-016"]] },
  it: { kicker:"Generatore", appTitle:"Etichette per scatole", appSub:"SVG in millimetri, foglio A4 con crocini di taglio.",
    labels:"Etichette", countsFmt:"{n} modello/i · {m} in totale", copies:"copie", duplicate:"Duplica", remove:"Elimina",
    addLabel:"+ Aggiungi un'etichetta", importSummary:"Importa un elenco incollato", importFormat:"Titolo | Sottotitolo | contenuto, contenuto | codice | data",
    importPh:"Una riga per etichetta", importBtn:"Sostituisci l'elenco", tab1:"1 · Contenuto", tab2:"2 · Stile", tab3:"3 · Stampa",
    selected:"Etichetta selezionata", selHint:"Il titolo è obbligatorio. Lascia un campo vuoto per rimuoverlo: l'impaginazione si ricompone e il testo restante occupa lo spazio.",
    phTitle:"Titolo (obbligatorio)", phSub:"Sottotitolo", phContents:"Contenuto, separato da virgole o ritorni a capo", phCode:"Codice / n.", phDate:"Data",
    phQr:"Contenuto del QR (predefinito: il codice)", logo:"Logo / icona", none:"Nessuna", upload:"Upload", searchPh:"cerca un'icona…", applyAll:"Applica questa icona a tutte",
    sizeHdr:"Dimensione dell'etichetta", w:"Larghezza mm", h:"Altezza mm", pad:"Margine interno mm", align:"Allineamento del testo", left:"Sinistra", center:"Centrato",
    borderHdr:"Bordo e colori", bw:"Spessore bordo mm", br:"Raggio angoli mm", border:"Bordo", bg:"Sfondo", ink:"Testo e icona",
    typoHdr:"Tipografia", font:"Carattere del testo", titlePt:"Titolo pt", subPt:"Sottotitolo pt", bodyPt:"Elenco pt", listStyle:"Disposizione dell'elenco",
    optLines:"Una riga per elemento", optInline:"Su una riga (· separatore)",
    colHdr:"Colonna dell'icona e separatori", colW:"Larghezza colonna mm", gapCol:"Spazio prima del testo mm", iconSolo:"Icona senza QR mm", iconQR:"Icona con QR mm",
    divW:"Spessore della linea mm", chkDiv:"Mostra le linee di separazione", chkFit:"Adatta il testo all'altezza", qrNote:"(sotto l'icona)",
    printHdr:"Foglio A4", modeLbl:"Cosa viene stampato", modeAll:"Tutte le etichette dell'elenco", modeOne:"Solo l'etichetta selezionata",
    fillFmt:"La pagina viene riempita automaticamente con l'etichetta selezionata ({n} per A4).", mx:"Margine sx/dx mm", my:"Margine alto/basso mm", gap:"Spazio tra etichette mm", cut:"Crocini di taglio",
    gridFmt:"{c} × {r} = {p} etichette per pagina A4 · {t} in totale", btnSvg:"SVG (1 etichetta)", btnSheet:"SVG foglio", btnPrint:"Stampa / PDF A4",
    editFmt:"Modifica — {s} · zoom {z}", realHdr:"Dimensione reale", byLabel:"Per etichetta", fullPage:"Pagina intera", pagesFmt:"{n} pagina/e",
    noTitle:"(senza titolo)", newLabel:"Nuova etichetta", srcNone:"nessuna", srcFile:"file",
    demo:[["Cavi e caricatori","Ufficio — mensola alta","USB-C, HDMI, jack 3.5","B-014"],["Utensili a mano","Officina","Pinze, cacciaviti, chiavi","B-015"],["Cartoleria","Ufficio","Penne, quaderni, foglietti","B-016"]] },
  pt: { kicker:"Gerador", appTitle:"Etiquetas de caixas", appSub:"SVG em milímetros, folha A4 com marcas de corte.",
    labels:"Etiquetas", countsFmt:"{n} modelo(s) · {m} no total", copies:"cópias", duplicate:"Duplicar", remove:"Eliminar",
    addLabel:"+ Adicionar uma etiqueta", importSummary:"Importar uma lista colada", importFormat:"Título | Subtítulo | conteúdo, conteúdo | código | data",
    importPh:"Uma linha por etiqueta", importBtn:"Substituir a lista", tab1:"1 · Conteúdo", tab2:"2 · Estilo", tab3:"3 · Impressão",
    selected:"Etiqueta selecionada", selHint:"O título é obrigatório. Deixe um campo vazio para o retirar: o layout recompõe-se e o texto restante ocupa o espaço.",
    phTitle:"Título (obrigatório)", phSub:"Subtítulo", phContents:"Conteúdo, separado por vírgulas ou mudanças de linha", phCode:"Código / n.º", phDate:"Data",
    phQr:"Conteúdo do QR (padrão: o código)", logo:"Logo / ícone", none:"Nenhum", upload:"Upload", searchPh:"procurar um ícone…", applyAll:"Aplicar este ícone a todas",
    sizeHdr:"Tamanho da etiqueta", w:"Largura mm", h:"Altura mm", pad:"Margem interior mm", align:"Alinhamento do texto", left:"Esquerda", center:"Centrado",
    borderHdr:"Contorno e cores", bw:"Espessura do contorno mm", br:"Raio dos cantos mm", border:"Contorno", bg:"Fundo", ink:"Texto e ícone",
    typoHdr:"Tipografia", font:"Tipo de letra", titlePt:"Título pt", subPt:"Subtítulo pt", bodyPt:"Lista pt", listStyle:"Disposição da lista",
    optLines:"Uma linha por elemento", optInline:"Na mesma linha (· separador)",
    colHdr:"Coluna do ícone e separadores", colW:"Largura da coluna mm", gapCol:"Espaço antes do texto mm", iconSolo:"Ícone sem QR mm", iconQR:"Ícone com QR mm",
    divW:"Espessura da linha mm", chkDiv:"Mostrar as linhas de separação", chkFit:"Ajustar o texto à altura", qrNote:"(abaixo do ícone)",
    printHdr:"Folha A4", modeLbl:"O que é impresso", modeAll:"Todas as etiquetas da lista", modeOne:"Apenas a etiqueta selecionada",
    fillFmt:"A página é preenchida automaticamente com a etiqueta selecionada ({n} por A4).", mx:"Margem esq./dir. mm", my:"Margem sup./inf. mm", gap:"Espaço entre etiquetas mm", cut:"Marcas de corte",
    gridFmt:"{c} × {r} = {p} etiquetas por página A4 · {t} no total", btnSvg:"SVG (1 etiqueta)", btnSheet:"SVG folha", btnPrint:"Imprimir / PDF A4",
    editFmt:"Edição — {s} · zoom {z}", realHdr:"Tamanho real", byLabel:"Por etiqueta", fullPage:"Página inteira", pagesFmt:"{n} página(s)",
    noTitle:"(sem título)", newLabel:"Nova etiqueta", srcNone:"nenhum", srcFile:"ficheiro",
    demo:[["Cabos e carregadores","Escritório — prateleira alta","USB-C, HDMI, jack 3.5","B-014"],["Ferramentas manuais","Oficina","Alicates, chaves de fendas, chaves","B-015"],["Papelaria","Escritório","Canetas, cadernos, notas","B-016"]] },
  nl: { kicker:"Generator", appTitle:"Doosetiketten", appSub:"SVG in millimeters, A4-vel met snijlijnen.",
    labels:"Etiketten", countsFmt:"{n} sjabloon/sjablonen · {m} in totaal", copies:"exemplaren", duplicate:"Dupliceren", remove:"Verwijderen",
    addLabel:"+ Etiket toevoegen", importSummary:"Een geplakte lijst importeren", importFormat:"Titel | Ondertitel | inhoud, inhoud | code | datum",
    importPh:"Eén regel per etiket", importBtn:"Lijst vervangen", tab1:"1 · Inhoud", tab2:"2 · Stijl", tab3:"3 · Afdrukken",
    selected:"Geselecteerd etiket", selHint:"Titel is verplicht. Laat een veld leeg om het weg te laten: de opmaak wordt herschikt en de resterende tekst vult de ruimte.",
    phTitle:"Titel (verplicht)", phSub:"Ondertitel", phContents:"Inhoud, gescheiden door komma's of regeleinden", phCode:"Code / nr.", phDate:"Datum",
    phQr:"QR-inhoud (standaard: de code)", logo:"Logo / pictogram", none:"Geen", upload:"Upload", searchPh:"pictogram zoeken…", applyAll:"Dit pictogram op alle toepassen",
    sizeHdr:"Etiketformaat", w:"Breedte mm", h:"Hoogte mm", pad:"Binnenmarge mm", align:"Tekstuitlijning", left:"Links", center:"Gecentreerd",
    borderHdr:"Rand & kleuren", bw:"Randdikte mm", br:"Hoekradius mm", border:"Rand", bg:"Achtergrond", ink:"Tekst & pictogram",
    typoHdr:"Typografie", font:"Lettertype", titlePt:"Titel pt", subPt:"Ondertitel pt", bodyPt:"Lijst pt", listStyle:"Lijstindeling",
    optLines:"Eén regel per item", optInline:"Op één regel (· scheidingsteken)",
    colHdr:"Pictogramkolom & scheidingslijnen", colW:"Kolombreedte mm", gapCol:"Ruimte voor tekst mm", iconSolo:"Pictogram zonder QR mm", iconQR:"Pictogram met QR mm",
    divW:"Lijndikte mm", chkDiv:"Scheidingslijnen weergeven", chkFit:"Tekstgrootte aan de hoogte aanpassen", qrNote:"(onder het pictogram)",
    printHdr:"A4-vel", modeLbl:"Wat wordt afgedrukt", modeAll:"Alle etiketten in de lijst", modeOne:"Alleen het geselecteerde etiket",
    fillFmt:"De pagina wordt automatisch gevuld met het geselecteerde etiket ({n} per A4).", mx:"Marge links/rechts mm", my:"Marge boven/onder mm", gap:"Ruimte tussen etiketten mm", cut:"Snijlijnen",
    gridFmt:"{c} × {r} = {p} etiketten per A4-pagina · {t} in totaal", btnSvg:"SVG (1 etiket)", btnSheet:"SVG vel", btnPrint:"Afdrukken / PDF A4",
    editFmt:"Bewerken — {s} · zoom {z}", realHdr:"Werkelijke grootte", byLabel:"Per etiket", fullPage:"Hele pagina", pagesFmt:"{n} pagina('s)",
    noTitle:"(zonder titel)", newLabel:"Nieuw etiket", srcNone:"geen", srcFile:"bestand",
    demo:[["Kabels & laders","Kantoor — bovenste schap","USB-C, HDMI, jack 3.5","B-014"],["Handgereedschap","Werkplaats","Tangen, schroevendraaiers, sleutels","B-015"],["Kantoorartikelen","Kantoor","Pennen, schriften, memoblaadjes","B-016"]] }
};
const LANGS = [
  { code: "fr", name: "Français", dir: "row", bands: ["#0055A4", "#FFFFFF", "#EF4135"] },
  { code: "en", name: "English (US)", us: true },
  { code: "es", name: "Español", dir: "column", bands: ["#AA151B", "#F1BF00", "#AA151B"] },
  { code: "de", name: "Deutsch", dir: "column", bands: ["#000000", "#DD0000", "#FFCE00"] },
  { code: "it", name: "Italiano", dir: "row", bands: ["#008C45", "#F4F5F0", "#CD212A"] },
  { code: "pt", name: "Português", dir: "row", bands: ["#006600", "#FF0000", "#FF0000"] },
  { code: "nl", name: "Nederlands", dir: "column", bands: ["#AE1C28", "#FFFFFF", "#21468B"] }
];
const detectLang = () => {
  const l = (navigator.languages && navigator.languages[0]) || navigator.language || "fr";
  const c = String(l).slice(0, 2).toLowerCase();
  return DICT[c] ? c : "en";
};
const fmt = (s, vals) => String(s || "").replace(/\{(\w+)\}/g, (m, k) => (vals[k] == null ? m : vals[k]));

const newRow = (o) => Object.assign({ title: "", subtitle: "", contents: "", code: "", date: "", qrText: "", n: 1, iSrc: "none", iD: "", iVB: "0 0 24 24", iUrl: "", iName: "" }, o || {});

// ---------- strings added or corrected since the export (docs/review.md) ----------
// The block above stays byte-identical to the export; every change to its texts is listed here.
const DICT_FIXES = {
  fr: { rangeFmt: "Entre {min} et {max}", searching: "Chargement…", noResults: "Aucun picto ne correspond.", upload: "Importer" },
  en: { rangeFmt: "Between {min} and {max}", searching: "Loading…", noResults: "No icon matches.", upload: "Upload" },
  es: { rangeFmt: "Entre {min} y {max}", searching: "Cargando…", noResults: "Ningún icono coincide.", upload: "Subir" },
  de: { rangeFmt: "Zwischen {min} und {max}", searching: "Wird geladen…", noResults: "Kein Symbol gefunden.", upload: "Hochladen" },
  it: { rangeFmt: "Tra {min} e {max}", searching: "Caricamento…", noResults: "Nessuna icona corrisponde.", upload: "Carica" },
  pt: { rangeFmt: "Entre {min} e {max}", searching: "A carregar…", noResults: "Nenhum ícone corresponde.", upload: "Carregar" },
  nl: { rangeFmt: "Tussen {min} en {max}", searching: "Laden…", noResults: "Geen pictogram gevonden.", upload: "Uploaden" }
};
for (const code in DICT_FIXES) Object.assign(DICT[code], DICT_FIXES[code]);

// ---------- bounds of the numeric fields (review B4, I14) ----------
// [min, max] from the other fields: the label always fits on the A4 sheet, inside its margins.
const BOUNDS = {
  w: s => [Math.max(10, 2 * s.pad + 2), 210 - 2 * s.mx],
  h: s => [Math.max(10, 2 * s.pad + 2), 297 - 2 * s.my],
  mx: s => [0, Math.min(50, (210 - s.w) / 2)],
  my: s => [0, Math.min(50, (297 - s.h) / 2)],
  pad: s => [0, Math.min(s.w, s.h) / 2 - 1],
  bw: () => [0, 5],
  br: s => [0, Math.min(s.w, s.h) / 2],
  titlePt: () => [4, 72],
  subPt: () => [4, 72],
  bodyPt: () => [4, 72],
  colW: s => [4, Math.max(4, s.w - 2 * s.pad - 12)],
  gapCol: () => [0, 20],
  iconSizeSolo: () => [1, 100],
  iconSize: () => [1, 100],
  divW: () => [0, 2],
  gap: () => [0, 20]
};
const MAX_COPIES = 999;

// Props of the design component, fixed at their defaults.
const PROPS = { startMode: "batch", showSheetPreview: true, defaultFont: "Archivo" };

const state = {
  w: 90, h: 50, pad: 5, align: "left",
  bw: 0.4, br: 3, borderColor: "#1b1917", bg: "#ffffff", fg: "#1b1917",
  font: "Archivo", titlePt: 15, subPt: 9, bodyPt: 8, listStyle: "lines",
  iconSize: 14, iconSizeSolo: 26, colW: 20, gapCol: 3, divider: true, divW: 0.3, autoFit: true,
  iconQuery: "", mdi: null, results: [], searching: false,
  qr: false,
  mode: "batch", repeat: 10,
  rows: [
    newRow({ title: "Câbles & chargeurs", subtitle: "Bureau — étagère haute", contents: "USB-C, HDMI, Jack 3.5", code: "B-014", date: "09/2026" }),
    newRow({ title: "Outils à main", subtitle: "Atelier", contents: "Pinces, tournevis, clés", code: "B-015", date: "09/2026" }),
    newRow({ title: "Papeterie", subtitle: "Bureau", contents: "Stylos, carnets, post-it", code: "B-016", date: "09/2026" })
  ],
  sel: 0, pasteText: "", tab: "content", realView: "label", lang: detectLang(), langOpen: false,
  mx: 8, my: 10, gap: 3, cut: true,
  fontReady: 0
};

// ---------- state ----------
// Text typed in a numeric field that is empty or out of bounds: shown and flagged, never applied.
const drafts = {};
function bounds(k, s) { const [lo, hi] = BOUNDS[k](s); return [lo, Math.max(lo, hi)]; }
function inBounds(k, v, s) { const [lo, hi] = bounds(k, s); return Number.isFinite(v) && v >= lo && v <= hi; }
// The state with every numeric field clamped into its bounds: all geometry reads this.
function S() {
  const s = Object.assign({}, state);
  for (const k in BOUNDS) { const [lo, hi] = bounds(k, s); s[k] = Math.min(Math.max(+s[k], lo), hi); }
  return s;
}
let renderQueued = false;
function setState(patch) {
  const next = typeof patch === "function" ? patch(state) : patch;
  if (next) Object.assign(state, next);
  if (!renderQueued) {
    renderQueued = true;
    queueMicrotask(() => { renderQueued = false; render(); });
  }
}

// ---------- helpers ----------
const FONT_CSS = (f) => "vendor/fonts/" + f.toLowerCase().replace(/\s+/g, "-") + ".css";
function loadFont(f) {
  const id = "gf-" + f.replace(/\s+/g, "-");
  if (!document.getElementById(id)) {
    const l = document.createElement("link");
    l.id = id; l.rel = "stylesheet";
    l.href = FONT_CSS(f);
    document.head.appendChild(l);
  }
  if (document.fonts) {
    Promise.all([document.fonts.load('400 16px "' + f + '"'), document.fonts.load('700 16px "' + f + '"')])
      .then(() => setState(s => ({ fontReady: s.fontReady + 1 }))).catch(() => {});
  }
}
function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
let measureCtx = null;
function measure(t, sizeMM, weight) {
  if (!measureCtx) measureCtx = document.createElement("canvas").getContext("2d");
  measureCtx.font = weight + " " + (sizeMM * 10) + 'px "' + state.font + '", sans-serif';
  return measureCtx.measureText(t).width / 10;
}
// Breaks at ASCII whitespace only: a no-break space (U+00A0) keeps two words together (review M9).
function wrap(t, maxMM, sizeMM, weight) {
  const words = String(t).split(/[ \t\n\r]+/).filter(Boolean);
  const lines = []; let cur = "";
  for (const wd of words) {
    const test = cur ? cur + " " + wd : wd;
    if (cur && measure(test, sizeMM, weight) > maxMM) { lines.push(cur); cur = wd; } else cur = test;
  }
  if (cur) lines.push(cur);
  return lines;
}
function splitList(t) { return String(t || "").split(/[\n,;]+/).map(x => x.trim()).filter(Boolean); }

// ---------- svg pieces ----------
function hasIcon(it) { return (it.iSrc === "upload" && !!it.iUrl) || !!it.iD; }
function iconMarkup(it, x, y, size) {
  if (it.iSrc === "upload" && it.iUrl)
    return '<image x="' + x + '" y="' + y + '" width="' + size + '" height="' + size + '" preserveAspectRatio="xMidYMid meet" href="' + it.iUrl + '"></image>';
  if (it.iD) {
    const vb = (it.iVB || "0 0 24 24").split(/\s+/).map(Number);
    const k = size / Math.max(vb[2], vb[3]);
    return '<g transform="translate(' + x + ',' + y + ') scale(' + k + ') translate(' + (-vb[0]) + ',' + (-vb[1]) + ')" fill="' + state.fg + '"><path d="' + it.iD + '"></path></g>';
  }
  return "";
}
function qrMarkup(text, size, x, y) {
  if (!window.QRCode || !text) return "";
  try {
    const q = new window.QRCode({ content: String(text), padding: 0, width: 100, height: 100, color: state.fg, background: "transparent", ecl: "M", join: true, container: "svg-viewbox" });
    const inner = q.svg().replace(/<svg[^>]*>/, "").replace(/<\/svg>/, "");
    return '<g transform="translate(' + x + ',' + y + ') scale(' + (size / 100) + ')">' + inner + "</g>";
  } catch (e) { return ""; }
}

function buildInner(it) {
  const s = S(), W = +s.w, H = +s.h, pad = +s.pad, bw = +s.bw;
  const o = [];
  o.push('<rect x="' + (bw / 2) + '" y="' + (bw / 2) + '" width="' + Math.max(0, W - bw) + '" height="' + Math.max(0, H - bw) +
    '" rx="' + s.br + '" fill="' + s.bg + '"' + (bw > 0 ? ' stroke="' + s.borderColor + '" stroke-width="' + bw + '"' : ' stroke="none"') + "/>");

  const avail = H - 2 * pad;
  const withIcon = hasIcon(it);
  const qrText = it.qrText || it.code || it.title;
  const hasQR = !!s.qr && !!qrText && !!window.QRCode;
  const showCol = withIcon || hasQR;
  const colW = showCol ? Math.max(4, Math.min(+s.colW || 20, W - 2 * pad - 12)) : 0;
  const gapCol = showCol ? Math.max(0, +s.gapCol || 0) : 0;
  const ink = s.fg;

  if (showCol) {
    const divX = pad + colW + gapCol / 2;
    if (s.divider && +s.divW > 0)
      o.push('<line x1="' + divX + '" y1="' + pad + '" x2="' + divX + '" y2="' + (H - pad) + '" stroke="' + ink + '" stroke-width="' + s.divW + '" opacity="0.55"/>');
    if (withIcon && hasQR) {
      const midY = pad + avail / 2;
      if (s.divider && +s.divW > 0)
        o.push('<line x1="' + pad + '" y1="' + midY + '" x2="' + (pad + colW) + '" y2="' + midY + '" stroke="' + ink + '" stroke-width="' + s.divW + '" opacity="0.55"/>');
      const cellH = avail / 2 - gapCol / 2;
      const isz = Math.min(colW, cellH, +s.iconSize || 99);
      o.push(iconMarkup(it, pad + (colW - isz) / 2, pad + (cellH - isz) / 2, isz));
      const qsz = Math.min(colW, cellH);
      o.push(qrMarkup(qrText, qsz, pad + (colW - qsz) / 2, midY + gapCol / 2 + (cellH - qsz) / 2));
    } else if (withIcon) {
      const isz = Math.min(colW, avail, +s.iconSizeSolo || 99);
      o.push(iconMarkup(it, pad + (colW - isz) / 2, pad + (avail - isz) / 2, isz));
    } else {
      const qsz = Math.min(colW, avail);
      o.push(qrMarkup(qrText, qsz, pad + (colW - qsz) / 2, pad + (avail - qsz) / 2));
    }
  }

  const tx = pad + (showCol ? colW + gapCol : 0);
  const tw = Math.max(6, W - pad - tx);
  const list = splitList(it.contents);
  const foot = [it.code, it.date].filter(Boolean).join("   ");

  // Every line advances 1.2 x its size in put() below, so the estimate uses 1.2 too (review M8).
  // w is the widest line, footer included: a label fits when both its height and its width do (I3).
  const layout = (k) => {
    const tS = s.titlePt * PT * k, sS = s.subPt * PT * k, bS = s.bodyPt * PT * k, fS = Math.max(4.5, s.bodyPt * 0.88) * PT * k;
    const tl = it.title ? wrap(it.title, tw, tS, "700") : [];
    const sl = it.subtitle ? wrap(it.subtitle, tw, sS, "400") : [];
    let ll = [];
    if (list.length) {
      // the separator sticks to the next item: a line never ends with a lone "·" (M9)
      if (s.listStyle === "inline") ll = wrap(list.join(" ·\u00a0"), tw, bS, "400");
      else list.forEach(x => wrap("· " + x, tw, bS, "400").forEach(l => ll.push(l)));
    }
    let h = tl.length * tS * 1.2;
    if (sl.length) h += tS * 0.35 + sl.length * sS * 1.2;
    if (ll.length) h += Math.max(1, bS * 0.9) + ll.length * bS * 1.2;
    if (foot) h += Math.max(1.2, fS * 1.1) + fS * 1.2;
    const widths = tl.map(l => measure(l, tS, "700")).concat(sl.map(l => measure(l, sS, "400")), ll.map(l => measure(l, bS, "400")));
    if (foot) widths.push(measure(foot, fS, "500"));
    return { h, w: Math.max(0, ...widths), tl, sl, ll, tS, sS, bS, fS };
  };
  const fits = (L) => L.h <= avail && L.w <= tw;

  let k = 1;
  if (s.autoFit) {
    let lo = 0.5, hi = 2.4;
    for (let i = 0; i < 14; i++) { const mid = (lo + hi) / 2; if (fits(layout(mid))) lo = mid; else hi = mid; }
    k = lo;
  } else if (!fits(layout(1))) {
    let lo = 0.5, hi = 1;
    for (let i = 0; i < 12; i++) { const mid = (lo + hi) / 2; if (fits(layout(mid))) lo = mid; else hi = mid; }
    k = lo;
  }

  const L = layout(k);
  const anchor = s.align === "center" ? "middle" : "start";
  const ax = s.align === "center" ? tx + tw / 2 : tx;
  let ty = pad + Math.max(0, (avail - L.h) / 2);
  const put = (t, size, weight, opacity, mono) => {
    ty += size * 0.88;
    o.push('<text x="' + ax + '" y="' + ty + '" text-anchor="' + anchor + '" font-family="' + esc(s.font) + ', ' + (mono ? "monospace" : "sans-serif") + '" font-weight="' + weight + '" font-size="' + size + '" fill="' + ink + '"' + (opacity ? ' opacity="' + opacity + '"' : "") + (mono ? ' letter-spacing="0.04" xml:space="preserve"' : "") + ">" + esc(t) + "</text>");
    ty += size * 0.32;
  };

  L.tl.forEach(l => put(l, L.tS, "700"));
  if (L.sl.length) { ty += L.tS * 0.35; L.sl.forEach(l => put(l, L.sS, "400", 0.72)); }
  if (L.ll.length) { ty += Math.max(1, L.bS * 0.9); L.ll.forEach(l => put(l, L.bS, "400", 0.9)); }
  if (foot) { ty += Math.max(1.2, L.fS * 1.1); put(foot, L.fS, "500", 0.65, true); }

  return o.join("");
}

function labelSVG(it, sized) {
  const s = S();
  const dim = sized === false ? 'width="100%" height="100%"' : 'width="' + s.w + 'mm" height="' + s.h + 'mm"';
  return '<svg xmlns="http://www.w3.org/2000/svg" ' + dim + ' viewBox="0 0 ' + s.w + " " + s.h + '">' + buildInner(it) + "</svg>";
}

function selIndex() { return Math.max(0, Math.min(state.sel, state.rows.length - 1)); }
function activeItem() { return state.rows[selIndex()] || newRow(); }
function items() {
  const s = state;
  if (s.mode === "single") return Array.from({ length: grid().per }, () => activeItem());
  const out = [];
  s.rows.forEach(r => { for (let i = 0; i < Math.max(1, +r.n || 1); i++) out.push(r); });
  return out.length ? out : [activeItem()];
}
function grid() {
  const s = S(), g = +s.gap;
  const cols = Math.max(1, Math.floor((210 - 2 * s.mx + g) / (+s.w + g)));
  const rows = Math.max(1, Math.floor((297 - 2 * s.my + g) / (+s.h + g)));
  return { cols, rows, per: cols * rows };
}
// clipId must be unique in the document: sheets of the preview and of the print area share it.
function sheetSVG(pageItems, real, clipId) {
  const s = S(), W = +s.w, H = +s.h, g = +s.gap, { cols, rows } = grid();
  const totalW = cols * W + (cols - 1) * g, totalH = rows * H + (rows - 1) * g;
  const ox = Math.max(+s.mx, (210 - totalW) / 2), oy = Math.max(+s.my, (297 - totalH) / 2);
  // Each label is clipped to its own box: text that still overflows (a word longer than the label at the
  // smallest size) is cut instead of printing on the next label (review I3).
  const clip = clipId || "label-clip";
  const o = ['<rect width="210" height="297" fill="#ffffff"/>', '<defs><clipPath id="' + clip + '"><rect width="' + W + '" height="' + H + '"/></clipPath></defs>'];
  const marks = [];
  pageItems.forEach((it, i) => {
    const c = i % cols, r = Math.floor(i / cols);
    const x = ox + c * (W + g), y = oy + r * (H + g);
    o.push('<g transform="translate(' + x + ',' + y + ')" clip-path="url(#' + clip + ')">' + buildInner(it) + "</g>");
    if (s.cut) {
      [x, x + W].forEach(vx => marks.push('<line x1="' + vx + '" y1="0" x2="' + vx + '" y2="4"/><line x1="' + vx + '" y1="293" x2="' + vx + '" y2="297"/>'));
      [y, y + H].forEach(vy => marks.push('<line x1="0" y1="' + vy + '" x2="4" y2="' + vy + '"/><line x1="206" y1="' + vy + '" x2="210" y2="' + vy + '"/>'));
    }
  });
  if (marks.length) o.push('<g stroke="#111" stroke-width="0.12">' + marks.join("") + "</g>");
  // no height on the preview: "auto" is not a valid SVG length, the viewBox gives the ratio
  const dim = real ? 'width="210mm" height="297mm"' : 'width="100%"';
  return '<svg xmlns="http://www.w3.org/2000/svg" ' + dim + ' viewBox="0 0 210 297">' + o.join("") + "</svg>";
}
function pages() {
  const its = items(), per = grid().per, out = [];
  for (let i = 0; i < its.length; i += per) out.push(its.slice(i, i + per));
  return out.length ? out : [[]];
}

// ---------- handlers ----------
function patchRow(patch) {
  setState(s => {
    const rows = s.rows.slice(), i = Math.max(0, Math.min(s.sel, rows.length - 1));
    rows[i] = Object.assign({}, rows[i], patch);
    return { rows };
  });
}
function seedDemo(lang) {
  const demo = (DICT[lang] || DICT.fr).demo;
  setState(s => {
    const pristine = s.rows.length === 3 && s.rows.every((r, i) => {
      const any = Object.keys(DICT).some(k => DICT[k].demo[i] && DICT[k].demo[i][0] === r.title);
      return any && !r.iD && !r.iUrl;
    });
    if (!pristine) return {};
    return { rows: demo.map((d, i) => Object.assign({}, s.rows[i], { title: d[0], subtitle: d[1], contents: d[2], code: d[3] })) };
  });
}
// Only the answer to the latest search is shown: each keystroke starts a search, and an earlier, slower
// one used to overwrite the results of the last (review I10).
let searchSeq = 0;
async function runSearch(q, src) {
  const seq = ++searchSeq;
  const show = (results) => { if (seq === searchSeq) setState({ results, searching: false }); };
  q = String(q || "").trim().toLowerCase();
  if (src === "mdi") {
    let mdi = state.mdi;
    if (!mdi) {
      setState({ searching: true });
      try {
        const m = await import(new URL("vendor/mdi/mdi.js", document.baseURI).href);
        mdi = Object.keys(m).filter(k => k.startsWith("mdi")).map(k => ({ name: k.slice(3).replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase(), d: m[k], vb: "0 0 24 24" }));
        setState({ mdi });
      } catch (err) { show([]); return; }
    }
    show((q ? mdi.filter(i => i.name.includes(q)) : mdi).slice(0, 56));
    return;
  }
  if (src === "material") {
    setState({ searching: true });
    const names = (q ? MAT.filter(n => n.includes(q)) : MAT).slice(0, 42);
    const out = await Promise.all(names.map(async n => {
      if (materialCache[n]) return materialCache[n];
      try {
        const r = await fetch("vendor/material-symbols/" + n + ".svg");
        if (!r.ok) return null;
        const txt = await r.text();
        const doc = new DOMParser().parseFromString(txt, "image/svg+xml");
        const vb = doc.documentElement.getAttribute("viewBox") || "0 -960 960 960";
        const d = Array.from(doc.querySelectorAll("path")).map(p => p.getAttribute("d")).join(" ");
        const item = { name: n.replace(/_/g, " "), d, vb };
        materialCache[n] = item;
        return item;
      } catch (e) { return null; }
    }));
    show(out.filter(x => x && x.d));
  }
}
const materialCache = {};
function download(name, text, type) {
  const b = new Blob([text], { type: type || "image/svg+xml" });
  const u = URL.createObjectURL(b);
  const a = document.createElement("a");
  a.href = u; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(u), 3000);
}

// Handlers receive the element carrying data-action / data-on, like React's currentTarget.
const handlers = {
  setField(el) {
    const k = el.dataset.k;
    if (el.dataset.num) {
      const v = el.value === "" ? NaN : parseFloat(el.value);
      if (!inBounds(k, v, state)) { drafts[k] = el.value; setState({}); return; }
      delete drafts[k];
      setState({ [k]: v });
      return;
    }
    setState({ [k]: el.dataset.bool ? el.checked : el.value });
  },
  setContent(el) { patchRow({ [el.dataset.k]: el.value }); },
  toggleLang() { setState(s => ({ langOpen: !s.langOpen })); },
  pickLang(el) {
    const lang = el.dataset.code;
    setState({ lang, langOpen: false });
    seedDemo(lang);
  },
  setTab(el) { setState({ tab: el.dataset.tab }); },
  setRealView(el) { setState({ realView: el.dataset.v }); },
  selRow(el) { setState({ sel: +el.dataset.i }); },
  setRowN(el) {
    const i = +el.dataset.i, v = Math.min(MAX_COPIES, Math.max(1, parseInt(el.value, 10) || 1));
    setState(s => { const rows = s.rows.slice(); rows[i] = Object.assign({}, rows[i], { n: v }); return { rows }; });
  },
  addRow() {
    setState(s => {
      const base = s.rows[Math.min(s.sel, s.rows.length - 1)] || newRow();
      const rows = s.rows.concat([Object.assign({}, base, { title: (DICT[s.lang] || DICT.fr).newLabel, subtitle: "", contents: "", code: "", qrText: "", n: 1 })]);
      return { rows, sel: rows.length - 1 };
    });
  },
  dupRow(el) {
    const i = +el.dataset.i;
    setState(s => { const rows = s.rows.slice(); rows.splice(i + 1, 0, Object.assign({}, rows[i])); return { rows, sel: i + 1 }; });
  },
  delRow(el) {
    const i = +el.dataset.i;
    setState(s => {
      if (s.rows.length <= 1) return {};
      const rows = s.rows.slice(); rows.splice(i, 1);
      return { rows, sel: Math.max(0, Math.min(s.sel, rows.length - 1)) };
    });
  },
  importPaste() {
    const lines = String(state.pasteText || "").split(/\n/).map(l => l.trim()).filter(Boolean);
    if (!lines.length) return;
    const rows = lines.map(l => {
      const p = l.split(/\s*[|;\t]\s*/);
      return newRow({ title: p[0] || "", subtitle: p[1] || "", contents: p[2] || "", code: p[3] || "", date: p[4] || "", qrText: p[5] || "" });
    });
    setState({ rows, sel: 0, mode: "batch", pasteText: "" });
  },
  applyIconToAll() {
    const a = activeItem();
    const pick = { iSrc: a.iSrc, iD: a.iD, iVB: a.iVB, iUrl: a.iUrl, iName: a.iName };
    setState(s => ({ rows: s.rows.map(r => Object.assign({}, r, pick)) }));
  },
  setFont(el) { const f = el.value; setState({ font: f }); loadFont(f); },
  applyPreset(el) {
    const p = el.dataset.preset.split("x");
    delete drafts.w; delete drafts.h;
    setState({ w: +p[0], h: +p[1] });
  },
  setIconSource(el) {
    const src = el.dataset.src;
    if (src === "none") { searchSeq++; patchRow({ iSrc: "none", iD: "", iUrl: "", iName: "" }); setState({ results: [], searching: false }); return; }
    patchRow({ iSrc: src });
    runSearch(state.iconQuery, src);
  },
  setIconQuery(el) { const q = el.value; setState({ iconQuery: q }); runSearch(q, activeItem().iSrc); },
  pickIcon(el) { patchRow({ iD: el.dataset.d, iVB: el.dataset.vb, iName: el.dataset.name, iUrl: "" }); },
  onUpload(el) {
    const f = el.files && el.files[0];
    if (!f) return;
    const rd = new FileReader();
    rd.onload = () => { patchRow({ iSrc: "upload", iUrl: rd.result, iD: "", iName: f.name }); setState({ results: [] }); };
    rd.readAsDataURL(f);
  },
  exportSVG() { const s = S(); download("etiquette-" + s.w + "x" + s.h + "mm.svg", labelSVG(activeItem())); },
  exportSheetSVG() { download("planche-a4.svg", sheetSVG(pages()[0], true)); },
  exportPNG() {
    const s = S();
    const px = m => Math.round(m / 25.4 * 300);
    const svg = labelSVG(activeItem());
    const img = new Image();
    img.onload = () => {
      const c = document.createElement("canvas");
      c.width = px(+s.w); c.height = px(+s.h);
      const ctx = c.getContext("2d");
      ctx.fillStyle = s.bg; ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(img, 0, 0, c.width, c.height);
      c.toBlob(b => {
        const u = URL.createObjectURL(b);
        const a = document.createElement("a");
        a.href = u; a.download = "etiquette-" + s.w + "x" + s.h + "mm@300dpi.png"; a.click();
        setTimeout(() => URL.revokeObjectURL(u), 3000);
      });
    };
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  },
  doPrint() { window.print(); }
};

// ---------- view ----------
const US_STRIPES = ["#B22234", "#FFFFFF", "#B22234", "#FFFFFF", "#B22234", "#FFFFFF", "#B22234"];
function flagMarkup(l) {
  if (l.us)
    return '<span class="flag flag-us">' + US_STRIPES.map(b => '<span class="flag-band" style="background:' + b + '"></span>').join("") +
      '<span class="flag-canton"></span></span>';
  return '<span class="flag" style="flex-direction:' + (l.dir || "row") + '">' +
    l.bands.map(b => '<span class="flag-band" style="background:' + b + '"></span>').join("") + "</span>";
}

function viewValues() {
  const s = S();
  const g = grid(), total = items().length;
  const scale = Math.min(540 / Math.max(1, +s.w), 340 / Math.max(1, +s.h));
  const act = activeItem(), si = selIndex();
  const T = Object.assign({ sourceCode: SOURCE[s.lang] || SOURCE.en }, DICT[s.lang] || DICT.fr);
  // decimal separator of the current language: ×1,59 in French (review M14)
  const zoom = "×" + new Intl.NumberFormat(s.lang, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Math.round(scale / 3.7795 * 100) / 100);
  return {
    T, g, scale, act, si,
    countsLine: fmt(T.countsFmt, { n: s.rows.length, m: total }),
    fillLine: fmt(T.fillFmt, { n: g.per }),
    editLine: fmt(T.editFmt, { s: s.w + " × " + s.h + " mm", z: zoom }),
    gridInfo: fmt(T.gridFmt, { c: g.cols, r: g.rows, p: g.per, t: total }),
    selNo: si + 1,
    version: VERSION,
    iconSourceLabel: act.iSrc === "none" || !act.iSrc ? T.srcNone : act.iSrc === "upload" ? (act.iName || T.srcFile) : act.iSrc + (act.iName ? " · " + act.iName : ""),
    qr: s.qr,
    // an imported image shows as a thumbnail, a picked icon as its path (review M1)
    hasIcon: !!act.iD,
    hasUpload: act.iSrc === "upload" && !!act.iUrl,
    showIconSearch: act.iSrc === "mdi" || act.iSrc === "material",
    iconStatus: s.searching ? T.searching : s.results.length ? "" : T.noResults,
    hasIconStatus: s.searching || !s.results.length,
    isSingle: s.mode === "single",
    isRealLabel: s.realView === "label",
    isRealPage: s.realView === "page",
    pageInfo: fmt(T.pagesFmt, { n: pages().length })
  };
}

// Controlled inputs: write the state back into the element, as React does.
function setValue(el, v) {
  if (el.type === "checkbox") { el.checked = !!v; return; }
  const str = v == null ? "" : String(v);
  if (el.type === "number") { if ((v === 0 && el.value === "") || el.value != v) el.value = str; return; }
  if (el.value !== str) el.value = str;
}

function setHTML(el, html) {
  if (el.__html !== html) { el.innerHTML = html; el.__html = html; }
}

// A numeric field is in error while its typed text is not applied, or when another field moved its
// bounds past its value (the geometry then uses the clamped value).
function renderErrors(v) {
  const number = new Intl.NumberFormat(state.lang, { maximumFractionDigits: 2 });
  for (const el of $$("input[data-num]")) {
    const k = el.dataset.k, [lo, hi] = bounds(k, state);
    const bad = k in drafts || !inBounds(k, +state[k], state);
    const msg = document.getElementById("err-" + k);
    el.toggleAttribute("aria-invalid", bad);
    msg.hidden = !bad;
    msg.textContent = bad ? fmt(v.T.rangeFmt, { min: number.format(lo), max: number.format(hi) }) : "";
  }
}

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

// MDI content-copy: U+29C9 (the export's glyph) is in none of the site's fonts, so it fell back to
// whatever the system had.
const COPY_ICON = '<svg class="row-btn-icon" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" ' +
  'd="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"></path></svg>';

function renderRows(v) {
  const box = $(".rows");
  const s = state;
  while (box.children.length < s.rows.length) {
    const row = document.createElement("div");
    row.className = "row";
    row.innerHTML =
      '<button type="button" class="row-main" data-action="selRow"><span class="row-title"><span></span></span><span class="row-sub"><span></span></span></button>' +
      '<input type="number" min="1" max="' + MAX_COPIES + '" step="1" class="row-copies" data-on="setRowN">' +
      '<button type="button" class="row-btn" data-action="dupRow">' + COPY_ICON + "</button>" +
      '<button type="button" class="row-btn row-btn-remove" data-action="delRow">×</button>';
    box.appendChild(row);
  }
  while (box.children.length > s.rows.length) box.lastElementChild.remove();
  s.rows.forEach((r, i) => {
    const row = box.children[i];
    const [main, copies, dup, del] = row.children;
    for (const el of row.children) el.dataset.i = String(i);
    main.classList.toggle("is-selected", i === v.si);
    main.querySelector(".row-title span").textContent = r.title || v.T.noTitle;
    main.querySelector(".row-sub span").textContent = [r.code, r.subtitle].filter(Boolean).join(" · ");
    copies.title = v.T.copies;
    setValue(copies, r.n || 1);
    dup.title = v.T.duplicate;
    del.title = v.T.remove;
  });
}

function renderLang() {
  const cur = LANGS.find(l => l.code === state.lang);
  setHTML($(".lang-btn"), cur ? flagMarkup(cur) + "<span><span>" + cur.code.toUpperCase() + "</span></span>" : "");
  const menu = $(".lang-menu");
  menu.hidden = !state.langOpen;
  setHTML(menu, state.langOpen ? LANGS.map(l =>
    '<button type="button" class="lang-option' + (l.code === state.lang ? " is-current" : "") + '" data-code="' + l.code + '" data-action="pickLang">' +
    flagMarkup(l) + "<span><span>" + esc(l.name) + "</span></span></button>").join("") : "");
}

function renderIconGrid() {
  const box = $(".icon-grid");
  if (box.__results === state.results) return;
  box.__results = state.results;
  box.innerHTML = state.results.map(r =>
    '<button type="button" class="icon-cell" title="' + esc(r.name) + '" data-name="' + esc(r.name) + '" data-d="' + esc(r.d) + '" data-vb="' + esc(r.vb) +
    '" data-action="pickIcon"><svg viewBox="' + esc(r.vb) + '"><path d="' + esc(r.d) + '" fill="currentColor"></path></svg></button>').join("");
  box.__html = undefined;
}

function render() {
  const s = state, c = S(), v = viewValues();
  for (const el of $$("[data-t]")) el.textContent = v.T[el.dataset.t];
  for (const el of $$("[data-ph]")) el.placeholder = v.T[el.dataset.ph];
  for (const el of $$("[data-bind]")) el.textContent = v[el.dataset.bind];
  // toggleAttribute, not el.hidden: SVG elements have no hidden property
  for (const el of $$("[data-if]")) el.toggleAttribute("hidden", !v[el.dataset.if]);
  for (const el of $$("[data-panel]")) el.hidden = el.dataset.panel !== s.tab;
  for (const el of $$(".tab")) el.classList.toggle("is-active", el.dataset.tab === s.tab);
  for (const el of $$(".seg-btn")) el.classList.toggle("is-active", el.dataset.v === s.realView);

  renderLang();
  renderRows(v);

  for (const el of $$("[data-k]")) {
    const k = el.dataset.k;
    const content = el.dataset.on === "setContent";
    if (!(k in drafts)) setValue(el, content ? (v.act[k] || "") : s[k]);
  }
  renderErrors(v);

  const icon = $(".logo-icon");
  icon.setAttribute("viewBox", v.act.iVB || "0 0 24 24");
  icon.firstElementChild.setAttribute("d", v.act.iD || "");
  const thumb = $(".logo-img");
  if (v.hasUpload && thumb.getAttribute("src") !== v.act.iUrl) thumb.setAttribute("src", v.act.iUrl);
  if (!v.hasUpload) thumb.removeAttribute("src");
  renderIconGrid();

  const preview = $(".label-preview");
  preview.style.width = "min(100%, " + (+c.w * v.scale) + "px)";
  preview.style.minWidth = "0";
  preview.style.aspectRatio = (+c.w) + " / " + (+c.h);
  setHTML(preview, labelSVG(v.act, false));

  if (v.isRealLabel) {
    const real = $(".label-real");
    real.style.width = (+c.w) + "mm";
    real.style.height = (+c.h) + "mm";
    real.style.flex = "0 0 auto";
    real.style.marginInline = (+c.w) / 25.4 * 96 <= 400 ? "auto" : "0";
    setHTML(real, labelSVG(v.act, false));
  }
  const pageList = pages();
  if (v.isRealPage) {
    setHTML($(".sheets"), PROPS.showSheetPreview === false ? "" :
      pageList.map((p, i) => '<div class="sheet">' + sheetSVG(p, false, "clip-preview-" + i) + "</div>").join(""));
  }
  setHTML($(".print-sheets"), pageList.map((p, i) => '<div class="print-sheet">' + sheetSVG(p, true, "clip-print-" + i) + "</div>").join(""));
}

// ---------- boot ----------
function onEvent(e) {
  const el = e.target.closest("[data-on]");
  if (!el) return;
  const onChange = el.tagName === "SELECT" || el.type === "checkbox" || el.type === "file";
  if ((e.type === "change") === onChange) handlers[el.dataset.on](el);
}

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-action]");
  if (el) handlers[el.dataset.action](el);
});
document.addEventListener("input", onEvent);
document.addEventListener("change", onEvent);

for (const el of $$("input[data-num]")) {
  const msg = document.createElement("span");
  msg.className = "fld-error";
  msg.id = "err-" + el.dataset.k;
  msg.hidden = true;
  el.setAttribute("aria-describedby", msg.id);
  el.after(msg);
}
$('[data-k="font"]').innerHTML = FONTS.map(f => '<option value="' + esc(f) + '">' + esc(f) + "</option>").join("");
if (PROPS.defaultFont !== state.font || PROPS.startMode !== state.mode) Object.assign(state, { font: PROPS.defaultFont, mode: PROPS.startMode });
render();
loadFont(state.font);
if (state.lang !== "fr") seedDemo(state.lang);
})();
