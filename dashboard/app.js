'use strict';
/* ============================================================
   Dye DAM Dashboard v2 — App Logic
   ============================================================ */

/* ---- Maintenance thresholds ---- */
const THRESHOLD_STANDARD = 5000;
const THRESHOLD_COMPLETE = 50000;
const TOTAL_STEPS = 8;

/* ============================================================
   PARTS DATA
   ============================================================ */
const PARTS = [
  { name: 'Canon Dye Ultralite 14"', ref: 'DYE-DAM-BRL-14', desc: 'Filetage Autococker ⅞-14 UNS. Compatible insert Freak. Anodisation type III.', qty: '×1', tag: 'crit', tagLabel: 'Critique', bg: '#1a3a5c', icon: '<rect x="3" y="16" width="34" height="8" rx="2" fill="#457b9d"/><circle cx="5" cy="20" r="4" fill="#2d6a8f"/>' },
  { name: 'Bolt OOPS (One Piece Spool)', ref: 'DYE-DAM-BOLT-01', desc: 'Spool monopiece, 3× O-rings NBR. Pression fonctionnement 165 PSI.', qty: '×1', tag: 'crit', tagLabel: 'Critique', bg: '#1a1a2e', icon: '<rect x="4" y="13" width="32" height="14" rx="4" fill="#e63946"/><rect x="6" y="16" width="10" height="8" rx="1" fill="#c1121f"/>' },
  { name: 'Régulateur Dye 2 étages', ref: 'DYE-DAM-REG-165', desc: 'Sortie 165 PSI usine. Inox + aluminium anodisé. Clé sangle requise.', qty: '×1', tag: 'imp', tagLabel: 'Important', bg: '#0d2013', icon: '<circle cx="20" cy="20" r="14" fill="none" stroke="#06d6a0" stroke-width="2.5"/><circle cx="20" cy="20" r="7" fill="#06d6a0" opacity=".6"/><circle cx="20" cy="20" r="3" fill="#06d6a0"/>' },
  { name: 'Solénoïde 3-Way', ref: 'DYE-DAM-SOL-3W', desc: 'Électrovanne 3 voies, 12V DC, temps réponse <4ms. PCB intégré.', qty: '×1', tag: 'imp', tagLabel: 'Important', bg: '#1a0d1a', icon: '<rect x="4" y="11" width="32" height="18" rx="3" fill="#0d1117" stroke="#457b9d" stroke-width="1.5"/><circle cx="28" cy="20" r="5" fill="#1a3a5c" stroke="#457b9d"/>' },
  { name: 'Kit O-rings complet (14 pcs)', ref: 'DYE-DAM-ORING-KIT', desc: 'NBR tailles #006→#014. Remplacement recommandé toutes les 50k billes.', qty: '×14', tag: 'cons', tagLabel: 'Consommable', bg: '#1a0000', icon: '<ellipse cx="20" cy="20" rx="13" ry="7" fill="none" stroke="#e63946" stroke-width="3"/><ellipse cx="20" cy="26" rx="13" ry="7" fill="none" stroke="#e63946" stroke-width="2" opacity=".4"/>' },
  { name: 'Batterie CR2 Lithium 3V', ref: 'CR2-3V-LITHIUM', desc: '3V lithium CR2. Autonomie ~50 000 billes. Lithium uniquement (pas alcaline).', qty: '×1', tag: 'cons', tagLabel: 'Consommable', bg: '#2d2000', icon: '<rect x="13" y="5" width="14" height="30" rx="4" fill="#2d2000" stroke="#ffd166" stroke-width="1.5"/><rect x="16" y="4" width="8" height="6" rx="2" fill="#ffd166" opacity=".7"/>' },
  { name: 'Chargeur Dye LTR / Rotor', ref: 'DYE-DAM-LTR-01', desc: 'Chargeur électronique haute cadence. Débit 30 bps recommandé pour DAM.', qty: '×1', tag: 'opt', tagLabel: 'Optionnel', bg: '#0d1a0d', icon: '<rect x="8" y="14" width="24" height="12" rx="3" fill="#0d2013" stroke="#06d6a0" stroke-width="1.5"/><rect x="14" y="5" width="12" height="10" rx="2" fill="#06d6a0" opacity=".7"/>' },
  { name: 'Magasin MAG 20 coups', ref: 'DYE-DAM-MAG-20', desc: 'Compatible First Strike & billes .68 standard. Système dual-feed DAM.', qty: '×1–2', tag: 'opt', tagLabel: 'Optionnel', bg: '#1a1200', icon: '<rect x="10" y="6" width="20" height="28" rx="3" fill="#1a1200" stroke="#ffd166" stroke-width="1.5"/><rect x="14" y="10" width="12" height="4" rx="1" fill="#ffd166" opacity=".5"/><rect x="14" y="17" width="12" height="4" rx="1" fill="#ffd166" opacity=".5"/>' },
  { name: 'Vis Allen Set (8 pcs)', ref: 'DYE-DAM-SCREW-KIT', desc: 'M2 ×4, 5/32" ×2, 3mm ×2. Inox. Remplacez toute vis stripée immédiatement.', qty: '×8', tag: 'imp', tagLabel: 'Important', bg: '#1a1a1a', icon: '<circle cx="20" cy="20" r="14" fill="#1a1a1a" stroke="#c8c8c8" stroke-width="2"/><line x1="20" y1="10" x2="20" y2="30" stroke="#c8c8c8" stroke-width="2.5"/><line x1="10" y1="20" x2="30" y2="20" stroke="#c8c8c8" stroke-width="2.5"/>' },
  { name: 'Dye Slick Lube', ref: 'DYE-LUBE-SL-01', desc: 'Graisse silicone pour O-rings et bolt. N\'utilisez jamais de WD-40 ou huile moteur.', qty: '×1', tag: 'cons', tagLabel: 'Consommable', bg: '#1a2800', icon: '<rect x="12" y="5" width="16" height="30" rx="5" fill="#1a2800" stroke="#06d6a0" stroke-width="1.5"/><text x="20" y="24" font-family="sans-serif" font-size="8" fill="#06d6a0" text-anchor="middle">DYE</text>' },
];

/* ============================================================
   DIAGNOSTIC TREE
   ============================================================ */
const TREE = {
  root: {
    q: 'Quel est le problème avec votre Dye DAM ?',
    opts: [
      { label: 'Le marqueur ne tire pas', icon: '🚫', next: 'no_fire' },
      { label: 'Fuite de gaz', icon: '💨', next: 'gas_leak' },
      { label: 'Tir irrégulier / vitesse anormale', icon: '📊', next: 'irregular' },
      { label: 'Problème électronique / LED', icon: '⚡', next: 'electric' },
      { label: 'Bruit anormal', icon: '🔊', next: 'noise' },
      { label: "Problème d'alimentation billes", icon: '🔵', next: 'feed' },
    ]
  },
  no_fire: {
    q: 'Que se passe-t-il quand vous appuyez sur la gâchette ?',
    opts: [
      { label: 'Rien du tout — aucun son', icon: '😶', next: 'no_power' },
      { label: 'Clic solénoïde, mais pas de bille', icon: '🔊', next: 'spool_jam' },
      { label: 'Gaz sort mais pas de bille', icon: '💨', next: 'low_pressure' },
    ]
  },
  no_power: {
    diag: true, sev: 'easy',
    title: 'Batterie CR2 déchargée',
    cause: 'Dans 90% des cas c\'est la batterie CR2 vide. L\'électrovanne (qui commande le gaz à chaque tir) ne reçoit plus de courant.',
    steps: ['Ouvrez le compartiment batterie sur la face gauche de la poignée — il s\'ouvre généralement en appuyant sur un bouton ou en dévissant un couvercle', 'Remplacez la batterie CR2 3V lithium (une petite pile cylindrique, différente des piles AA ou AAA classiques)', 'Allumez le lanceur — la LED verte doit clignoter 3 fois pour confirmer le bon fonctionnement', 'Si toujours rien après remplacement : vérifiez que le connecteur de l\'électrovanne est bien branché (voir Étape 4 du guide)'],
    fixStep: 4, parts: ['Batterie CR2 3V lithium']
  },
  spool_jam: {
    q: 'Depuis combien de temps n\'avez-vous pas lubrifié le percuteur interne ?',
    opts: [
      { label: 'Moins de 5 000 billes tirées', icon: '✅', next: 'spool_jam_other' },
      { label: 'Plus de 5 000 billes (ou je ne sais pas)', icon: '⚠️', next: 'spool_lubrication' },
    ]
  },
  spool_lubrication: {
    diag: true, sev: 'easy',
    title: 'Percuteur encrassé — Lubrification nécessaire',
    cause: 'Le percuteur interne (bolt OOPS) glisse à sec, ce qui crée des micro-frictions qui empêchent le cycle complet de tir.',
    steps: ['Retirez le capuchon arrière (2× vis clé hexagonale 3mm, face arrière du corps)', 'Sortez le percuteur, nettoyez ses 3 joints toriques avec un chiffon', 'Appliquez Dye Slick Lube sur chaque joint torique (une toute fine couche suffit)', 'Réinsérez le percuteur et testez à basse pression'],
    fixStep: 3, parts: ['Dye Slick Lube', 'Joint torique #009 (si endommagé)']
  },
  spool_jam_other: {
    diag: true, sev: 'medium',
    title: 'Obstruction — Débris ou fragment de bille coincé',
    cause: 'Un fragment de bille cassée ou un corps étranger bloque la chambre d\'alimentation, empêchant le percuteur de revenir en position.',
    steps: ['Déconnectez la bouteille de gaz immédiatement (dévissez-la)', 'Retirez le canon (quart de tour antihoraire) et inspectez le corps avec une lampe', 'Sortez le percuteur (capuchon arrière + 2 vis), inspectez le canal interne', 'Nettoyez avec un chiffon en microfibre propre + air comprimé si disponible', 'Vérifiez la qualité des billes (calibre .68 standard recommandé)'],
    fixStep: 3, parts: ['Chiffon microfibre', 'Air comprimé']
  },
  low_pressure: {
    diag: true, sev: 'medium',
    title: 'Pression insuffisante — Bouteille vide ou régulateur',
    cause: 'Le gaz arrive mais pas assez fort pour propulser la bille correctement. Votre bouteille d\'air comprimé est peut-être presque vide, ou le régulateur de pression a un problème.',
    steps: ['Vérifiez le niveau de votre bouteille de gaz (la pression doit dépasser 70 bars / 1000 PSI minimum)', 'Si la bouteille est pleine : démontez et remontez le régulateur de pression (Étape 6)', 'Vérifiez les 2 joints toriques d\'étanchéité du régulateur (entrée et sortie)', 'La pression de sortie du régulateur doit être de 160–175 PSI (11–12 bars) — mesurable avec un chronographe au terrain'],
    fixStep: 6, parts: ['Joint torique #010', 'Joint torique #012']
  },
  gas_leak: {
    q: 'D\'où provient la fuite de gaz ?',
    opts: [
      { label: 'À l\'avant, autour du canon', icon: '🔫', next: 'leak_barrel' },
      { label: 'À l\'arrière, au niveau de la bouteille de gaz ou du régulateur', icon: '⚙️', next: 'leak_reg' },
      { label: 'Au milieu, sur le corps ou la poignée', icon: '🏠', next: 'leak_body' },
      { label: 'Partout / je ne suis pas sûr', icon: '🤷', next: 'leak_test' },
    ]
  },
  leak_barrel: {
    diag: true, sev: 'easy',
    title: 'Joint torique du canon usé ou manquant',
    cause: 'Le petit joint en caoutchouc (joint torique) à la base du canon ne fait plus l\'étanchéité — le gaz s\'échappe autour du canon.',
    steps: ['Retirez le canon : saisissez-le, tournez d\'un quart de tour antihoraire, tirez vers l\'avant', 'Inspectez le petit joint torique noir à la base du canon (fissuré ? absent ? déformé ?)', 'Remplacez-le par un joint torique #006 légèrement lubrifié', 'Revissez le canon à la main jusqu\'à sentir le contact doux — pas besoin d\'outil'],
    fixStep: 2, parts: ['Joint torique #006']
  },
  leak_reg: {
    diag: true, sev: 'medium',
    title: 'Joints toriques du régulateur endommagés',
    cause: 'Les joints d\'étanchéité du régulateur de pression (la pièce ronde vissée sous l\'arrière du corps) sont usés ou compressés — le gaz s\'échappe à haute pression.',
    steps: ['Dépressurisez complètement : dévissez la bouteille de gaz, appuyez sur la gâchette plusieurs fois', 'Dévissez le régulateur avec la clé à sangle (sens antihoraire)', 'Remplacez les 2 joints toriques d\'étanchéité (un à l\'entrée, un à la sortie)', 'Lubrifiez les joints avec du Dye Slick Lube avant le remontage', 'Revissez et faites un test en ouvrant la bouteille à moitié pour vérifier l\'étanchéité'],
    fixStep: 6, parts: ['Joint torique #010', 'Joint torique #012']
  },
  leak_body: {
    diag: true, sev: 'medium',
    title: 'Joints toriques du percuteur — fuite interne',
    cause: 'Un ou plusieurs joints toriques du percuteur interne (bolt) laissent passer le gaz vers l\'extérieur du corps.',
    steps: ['Retirez le capuchon arrière (capuchon plat à l\'arrière du corps, 2 vis clé hexagonale 3mm)', 'Sortez le percuteur (tirez vers l\'arrière par sa petite poignée)', 'Inspectez les 3 joints toriques sous une bonne lumière — remplacez tout joint fissuré, aplati ou durci', 'Lubrifiez les 3 joints toriques avec Dye Slick Lube', 'Réinsérez le percuteur et testez'],
    fixStep: 3, parts: ['Joint torique #008', 'Joint torique #009', 'Joint torique #011']
  },
  leak_test: {
    diag: true, sev: 'info',
    title: 'Localisation de fuite — méthode eau savonneuse',
    cause: 'Pour trouver précisément d\'où vient la fuite, la méthode eau + savon est la plus simple et efficace.',
    steps: ['Mélangez quelques gouttes de liquide vaisselle dans un vaporisateur d\'eau', 'Vissez la bouteille de gaz et ouvrez-la lentement à moitié seulement', 'Vaporisez sur chaque joint : autour du canon, autour du régulateur, sur le capuchon arrière, sur la poignée', 'Des bulles apparaissent exactement à l\'endroit de la fuite', 'Revissez la bouteille et consultez la section correspondante dans ce diagnostic'],
    fixStep: null, parts: ['Eau savonneuse', 'Vaporisateur']
  },
  irregular: {
    q: 'Quel est le problème de tir ?',
    opts: [
      { label: 'Vitesse trop élevée (> 300 FPS)', icon: '🔴', next: 'fps_high' },
      { label: 'Vitesse trop basse ou inconstante', icon: '📉', next: 'fps_low' },
      { label: 'Double bille (2 billes à la fois)', icon: '⚠️', next: 'double_ball' },
      { label: 'Billes qui cassent dans le canon', icon: '💥', next: 'ball_break' },
    ]
  },
  fps_high: {
    diag: true, sev: 'warning',
    title: '⚠️ Vitesse trop élevée — Réglage immédiat requis',
    cause: 'Au-delà de 300 FPS (pieds par seconde, la vitesse des billes), vous risquez des blessures graves et une disqualification du terrain. La limite légale sur la plupart des terrains est 280–300 FPS.',
    steps: ['Accédez au menu électronique du lanceur (maintenez la gâchette appuyée 5 sec alors que le lanceur est éteint)', 'Naviguez dans le menu vers le réglage de vélocité (vitesse de tir)', 'Réduisez par petits crans de 5 FPS et mesurez à chaque fois au chronographe du terrain', 'Objectif : 280–290 FPS avec des billes .68 standard', 'Si le réglage électronique ne suffit pas : ajustez le régulateur de pression (Étape 6)'],
    fixStep: null, parts: []
  },
  fps_low: {
    diag: true, sev: 'medium',
    title: 'Vitesse insuffisante — Batterie ou joints toriques',
    cause: 'Batterie faible (l\'électrovanne réagit trop lentement) ou joints toriques du percuteur usés (fuite interne de gaz qui réduit la puissance de propulsion).',
    steps: ['Commencez par remplacer la batterie CR2 3V lithium (cause la plus fréquente)', 'Si ça ne change rien : démontez le percuteur (capuchon arrière + 2 vis) et inspectez ses 3 joints toriques', 'Vérifiez que votre bouteille de gaz n\'est pas presque vide (niveau recommandé : plus de 100 bars / 1500 PSI)', 'Nettoyez et relubrifiez complètement le percuteur et ses joints'],
    fixStep: 3, parts: ['Batterie CR2', 'Kit joints toriques percuteur']
  },
  double_ball: {
    diag: true, sev: 'medium',
    title: 'Capteur optique (Eye) encrassé',
    cause: 'Le détecteur d\'alimentation est obstrué par de la peinture ou des débris.',
    steps: ['Ouvrez le couvercle d\'accès aux yeux (2 vis sur le corps)', 'Nettoyez délicatement avec un coton-tige humide', 'Soufflez à l\'air comprimé (pression modérée)', 'Vérifiez l\'alignement des 2 capteurs infrarouges', 'Si persistant : activez temporairement le mode Blind Fire'],
    fixStep: null, parts: ['Coton-tiges', 'Air comprimé']
  },
  ball_break: {
    diag: true, sev: 'easy',
    title: 'Billes inadaptées ou alésage canon trop serré',
    cause: 'L\'alésage du canon est inadapté au diamètre des billes utilisées.',
    steps: ['Mesurez le diamètre de vos billes (.689, .690, .691…)', 'Vérifiez l\'insert Freak correspondant si équipé', 'Passez à des billes de qualité (Valken, GI Sportz)', 'Nettoyez le canon après chaque bourrage'],
    fixStep: 2, parts: ['Insert Freak calibré']
  },
  electric: {
    q: 'Que montre la LED d\'état ?',
    opts: [
      { label: 'LED rouge fixe ou clignotante rapide', icon: '🔴', next: 'led_red' },
      { label: 'LED verte — marqueur non réactif', icon: '🟢', next: 'led_green_issue' },
      { label: 'Aucune LED', icon: '⬛', next: 'no_led' },
      { label: 'LED orange / ambre', icon: '🟠', next: 'led_orange' },
    ]
  },
  led_red: {
    diag: true, sev: 'easy',
    title: 'Batterie faible — Remplacement immédiat',
    cause: 'LED rouge = batterie presque vide (tension sous 2,4V). L\'électrovanne ne s\'active plus correctement, ce qui peut causer des ratés ou des tirs incohérents.',
    steps: ['Remplacez la batterie CR2 3V lithium (attention : CR2, pas CR123 ni AA)', 'Utilisez uniquement des piles CR2 lithium — les versions alcalines ne durent pas et ne fournissent pas assez de puissance par temps froid', 'Après remplacement, la LED doit passer au vert — c\'est le signe que tout va bien', 'Autonomie normale d\'une pile CR2 lithium : environ 40 000 à 60 000 billes'],
    fixStep: null, parts: ['Batterie CR2 3V Lithium']
  },
  led_green_issue: {
    diag: true, sev: 'medium',
    title: 'Reset usine requis — Profil corrompu',
    cause: 'La carte électronique est dans un état incohérent (profil de tir corrompu).',
    steps: ['Éteignez le marqueur complètement', 'Maintenez la gâchette en allumant', 'Relâchez après 3 clignotements verts (reset usine)', 'Reprogrammez votre profil de tir depuis zéro'],
    fixStep: null, parts: []
  },
  no_led: {
    diag: true, sev: 'medium',
    title: 'Alimentation coupée — Batterie ou connecteur débranché',
    cause: 'Aucune LED = pas d\'alimentation électrique du tout. Causes possibles : batterie complètement morte, connecteur électrique débranché, ou court-circuit dû à de l\'humidité.',
    steps: ['Remplacez en priorité la batterie CR2 3V lithium', 'Ouvrez la poignée (2 vis latérales) et vérifiez que le connecteur de l\'électrovanne est bien enfoncé dans son socket', 'Inspectez la carte électronique (la plaquette verte) pour des traces de dépôts blancs ou brunâtres (signe de corrosion due à l\'humidité)', 'Si vous voyez de la corrosion : nettoyez délicatement avec un coton-tige imbibé d\'alcool isopropylique à 99%'],
    fixStep: 4, parts: ['Batterie CR2', 'Alcool isopropylique 99%']
  },
  led_orange: {
    diag: true, sev: 'easy',
    title: 'Mode sécurité activé',
    cause: 'Le marqueur est en mode demi-charge ou le safety électronique est engagé.',
    steps: ['Vérifiez la position du safety physique (côté droit)', 'Déverrouillez : OFF → maintenez gâchette 2 sec', 'Si LED orange persiste : reset usine'],
    fixStep: null, parts: []
  },
  noise: {
    q: 'Quel type de bruit anormal ?',
    opts: [
      { label: 'Claquement métallique fort lors du tir', icon: '🔨', next: 'clang' },
      { label: 'Sifflement continu (gaz)', icon: '🎵', next: 'hiss' },
      { label: 'Cliquetis quand on bouge le marqueur', icon: '🔔', next: 'rattle' },
    ]
  },
  clang: {
    diag: true, sev: 'easy',
    title: 'Percuteur à sec — Lubrification insuffisante',
    cause: 'Le percuteur interne (bolt) frappe les parois du tunnel sans lubrifiant. Bruit métallique fort = percuteur complètement à sec. Symptôme classique après une longue période sans utilisation.',
    steps: ['Démontez le percuteur : retirez le capuchon arrière (2 vis hexagonales 3mm sur la face arrière du corps)', 'Sortez le percuteur, appliquez Dye Slick Lube généreusement sur les 3 joints toriques et sur le corps du percuteur', 'Réinsérez et testez — après lubrification, le bruit de tir doit devenir plus sourd et régulier'],
    fixStep: 3, parts: ['Dye Slick Lube']
  },
  hiss: {
    diag: true, sev: 'medium',
    title: 'Fuite de gaz active — Localisez la source',
    cause: 'Sifflement = fuite continue détectée.',
    steps: ['Dépressurisez immédiatement', 'Retournez au diagnostic "Fuite de gaz" pour localiser précisément'],
    fixStep: null, parts: []
  },
  rattle: {
    diag: true, sev: 'easy',
    title: 'Vis desserrée',
    cause: 'Une vis s\'est desserrée à cause des vibrations répétées du tir. Normal après une journée de jeu intensive.',
    steps: ['Vérifiez toutes les vis hexagonales du lanceur avec vos clés (3mm, 5/32", 1,5mm)', 'Resserrez légèrement sans forcer — le corps est en aluminium et se dénature facilement si on serre trop', 'Priorité aux zones les plus sollicitées : le capuchon arrière, la poignée, et le rail de montage supérieur'],
    fixStep: 8, parts: ['Jeu de clés hexagonales']
  },
  feed: {
    q: 'Quel est le problème d\'alimentation ?',
    opts: [
      { label: 'Le chargeur ne tourne pas / ne charge pas', icon: '🔄', next: 'hopper_issue' },
      { label: 'Bourrage fréquent en magasin MAG', icon: '📦', next: 'mag_jam' },
    ]
  },
  hopper_issue: {
    diag: true, sev: 'easy',
    title: 'Problème de chargeur électronique',
    cause: 'Chargeur non alimenté, incompatible, ou col de connexion obstrué.',
    steps: ['Vérifiez la batterie du chargeur', 'Nettoyez le col de connexion chargeur/marqueur', 'Utilisez un chargeur compatible (Dye LTR ou Rotor recommandé)', 'Activez le mode "low profile hopper" si chargeur court'],
    fixStep: null, parts: []
  },
  mag_jam: {
    diag: true, sev: 'easy',
    title: 'Bourrage magasin — Ressort ou calibre billes',
    cause: 'Billes mal alignées ou ressort de poussoir fatigué.',
    steps: ['Retirez le MAG, libérez les billes manuellement', 'Inspectez le ressort de poussoir (doit être tendu)', 'Nettoyez le canal avec un chiffon', 'Rechargez lentement — ne tassez pas', 'Vérifiez calibre billes (.68 standard)'],
    fixStep: null, parts: []
  },
};

/* ============================================================
   STATE
   ============================================================ */
let state = {
  currentStep: 1,
  completedSteps: new Set(),
  notes: {},
  ballCount: 0,
  fpsHistory: [],
  maintenanceLog: [],
  diagPath: ['root'],
  isPlaying: false,
  timerInterval: null,
  timerSeconds: 0,
  timerRunning: false,
};

function loadState() {
  try {
    const s = JSON.parse(localStorage.getItem('dye-dam-v2') || '{}');
    if (s.completedSteps) state.completedSteps = new Set(s.completedSteps);
    if (s.notes) state.notes = s.notes;
    if (s.ballCount) state.ballCount = s.ballCount;
    if (s.fpsHistory) state.fpsHistory = s.fpsHistory;
    if (s.maintenanceLog) state.maintenanceLog = s.maintenanceLog;
  } catch(e) {}
}

function saveState() {
  localStorage.setItem('dye-dam-v2', JSON.stringify({
    completedSteps: [...state.completedSteps],
    notes: state.notes,
    ballCount: state.ballCount,
    fpsHistory: state.fpsHistory,
    maintenanceLog: state.maintenanceLog,
  }));
}

/* ============================================================
   UTILS
   ============================================================ */
function $(id) { return document.getElementById(id); }
function announce(msg) {
  const el = $('sr-announce');
  el.textContent = '';
  requestAnimationFrame(() => { el.textContent = msg; });
}
function showAlert(msg) {
  const b = $('alert-banner');
  $('alert-text').textContent = msg;
  b.hidden = false;
  clearTimeout(b._t);
  b._t = setTimeout(() => { b.hidden = true; }, 5000);
}
function formatNum(n) { return n.toLocaleString('fr-FR'); }
function today() { return new Date().toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' }); }

/* Smooth counter animation */
function animateCount(el, from, to, duration = 600) {
  const start = performance.now();
  const range = to - from;
  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = formatNum(Math.round(from + range * ease));
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ============================================================
   NAVIGATION
   ============================================================ */
const navBtns = document.querySelectorAll('.nav-btn');
const sections = document.querySelectorAll('.guide-section');
const toolbar  = $('toolbar');

navBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const id = btn.dataset.section;
    navBtns.forEach(b => { b.classList.remove('active'); b.setAttribute('aria-pressed', 'false'); });
    btn.classList.add('active');
    btn.setAttribute('aria-pressed', 'true');
    sections.forEach(s => s.classList.remove('active'));
    const sec = $(`section-${id}`);
    if (sec) sec.classList.add('active');
    toolbar.style.display = (id === 'demontage') ? '' : 'none';
    if (id === 'pieces') renderParts();
    if (id === 'carnet') renderCarnet();
    if (id === 'diagnostic') renderDiag();
  });
});

/* ============================================================
   STEP NAVIGATION
   ============================================================ */
function goToStep(n) {
  n = Math.max(1, Math.min(TOTAL_STEPS, n));
  state.currentStep = n;
  const cards = document.querySelectorAll('.step-card');

  cards.forEach((card, i) => {
    const sn = i + 1;
    card.classList.toggle('active', sn === n);
    if (sn === n) {
      card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      card.focus({ preventScroll: true });
    }
  });

  const pct = (n / TOTAL_STEPS) * 100;
  $('progress-fill').style.width = pct + '%';
  $('progress-bar').setAttribute('aria-valuenow', n);
  $('current-step').textContent = n;
  $('btn-prev').disabled = (n === 1);
  $('btn-next').disabled = (n === TOTAL_STEPS);
  updateDots();
  resetStepTimer();
}

function updateDots() {
  const dotsEl = $('step-dots');
  dotsEl.innerHTML = '';
  for (let i = 1; i <= TOTAL_STEPS; i++) {
    const d = document.createElement('div');
    d.className = 'step-dot';
    if (state.completedSteps.has(i)) d.classList.add('done');
    if (i === state.currentStep) d.classList.add('active');
    d.addEventListener('click', () => goToStep(i));
    d.setAttribute('title', `Étape ${i}`);
    dotsEl.appendChild(d);
  }
}

$('btn-prev').addEventListener('click', () => goToStep(state.currentStep - 1));
$('btn-next').addEventListener('click', () => goToStep(state.currentStep + 1));

/* ============================================================
   STEP TIMER
   ============================================================ */
function startStepTimer() {
  if (state.timerRunning) return;
  state.timerRunning = true;
  $('step-timer').classList.add('running');
  state.timerInterval = setInterval(() => {
    state.timerSeconds++;
    const m = String(Math.floor(state.timerSeconds / 60)).padStart(2, '0');
    const s = String(state.timerSeconds % 60).padStart(2, '0');
    $('step-timer').textContent = `${m}:${s}`;
  }, 1000);
}

function resetStepTimer() {
  clearInterval(state.timerInterval);
  state.timerRunning = false;
  state.timerSeconds = 0;
  $('step-timer').textContent = '00:00';
  $('step-timer').classList.remove('running');
}

document.querySelectorAll('.step-card').forEach(card => {
  card.addEventListener('click', e => {
    if (e.target.closest('.complete-btn, .note-btn, .step-note')) return;
    const sn = parseInt(card.dataset.step);
    if (sn !== state.currentStep) { goToStep(sn); }
    else if (!state.timerRunning) startStepTimer();
  });
  card.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      goToStep(parseInt(card.dataset.step));
    }
  });
});

/* ============================================================
   AUTO PLAY
   ============================================================ */
let autoInterval = null;

$('btn-play').addEventListener('click', () => {
  if (state.isPlaying) stopPlay(); else startPlay();
});

function startPlay() {
  state.isPlaying = true;
  const btn = $('btn-play');
  btn.classList.add('playing');
  btn.setAttribute('aria-pressed', 'true');
  btn.setAttribute('aria-label', 'Pause');
  $('play-icon').innerHTML = '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>';
  autoInterval = setInterval(() => {
    if (state.currentStep < TOTAL_STEPS) goToStep(state.currentStep + 1);
    else stopPlay();
  }, 4200);
}

function stopPlay() {
  state.isPlaying = false;
  clearInterval(autoInterval);
  const btn = $('btn-play');
  btn.classList.remove('playing');
  btn.setAttribute('aria-pressed', 'false');
  btn.setAttribute('aria-label', 'Lecture automatique');
  $('play-icon').innerHTML = '<polygon points="5 3 19 12 5 21 5 3"/>';
}

/* ============================================================
   STEP COMPLETION
   ============================================================ */
document.querySelectorAll('.complete-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    const n = parseInt(btn.dataset.step);
    const card = btn.closest('.step-card');
    if (state.completedSteps.has(n)) {
      state.completedSteps.delete(n);
      card.classList.remove('completed');
      announce(`Étape ${n} marquée non complétée.`);
    } else {
      state.completedSteps.add(n);
      card.classList.add('completed');
      announce(`Étape ${n} validée !`);
      if (n === state.currentStep && n < TOTAL_STEPS) {
        setTimeout(() => goToStep(n + 1), 450);
      }
    }
    $('stat-done').textContent = state.completedSteps.size;
    const done = state.completedSteps.size;
    $('progress-done').textContent = done > 0 ? `· ${done} validée${done > 1 ? 's' : ''}` : '';
    updateDots();
    saveState();
    if (state.completedSteps.size === TOTAL_STEPS) showCompleteToast();
  });
});

function showCompleteToast() {
  announce('Toutes les étapes validées ! Démontage complet.');
  showAlert('🎉 Démontage complet — Toutes les étapes validées !');
}

/* ============================================================
   NOTES
   ============================================================ */
document.querySelectorAll('.note-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    const n = btn.dataset.step;
    const area = $(`note-area-${n}`);
    const noteEl = $(`note-${n}`);
    const open = !area.hidden;
    area.hidden = open;
    btn.classList.toggle('active', !open);
    if (!open) { noteEl.value = state.notes[n] || ''; noteEl.focus(); }
  });
});

document.querySelectorAll('.step-note').forEach(ta => {
  ta.addEventListener('input', () => {
    const n = ta.id.replace('note-', '');
    state.notes[n] = ta.value;
    saveState();
  });
  ta.addEventListener('click', e => e.stopPropagation());
});

/* ============================================================
   BALL COUNTER
   ============================================================ */
function updateBallWidget(animated = false) {
  const el = $('bw-count');
  const prev = parseInt(el.textContent.replace(/\s/g, '')) || 0;
  if (animated) animateCount(el, prev, state.ballCount);
  else el.textContent = formatNum(state.ballCount);

  // Progress bar — cycle based on nearest threshold
  const cycleBase = state.ballCount < THRESHOLD_COMPLETE
    ? Math.floor(state.ballCount / THRESHOLD_STANDARD) * THRESHOLD_STANDARD
    : Math.floor(state.ballCount / THRESHOLD_COMPLETE) * THRESHOLD_COMPLETE;
  const cycleSize = state.ballCount < THRESHOLD_COMPLETE ? THRESHOLD_STANDARD : THRESHOLD_COMPLETE;
  const progress = ((state.ballCount - cycleBase) / cycleSize) * 100;
  $('bw-fill').style.width = Math.min(progress, 100) + '%';
  $('bw-progress').setAttribute('aria-valuenow', state.ballCount % cycleSize);

  // Next maintenance text
  const toStandard = THRESHOLD_STANDARD - (state.ballCount % THRESHOLD_STANDARD);
  const toComplete = THRESHOLD_COMPLETE - (state.ballCount % THRESHOLD_COMPLETE);
  const nearest = toStandard <= toComplete ? toStandard : toComplete;
  const type = toStandard <= toComplete ? 'standard' : 'complet';
  $('bw-next').textContent = `→ entretien ${type} dans ${formatNum(nearest)}`;

  // Alert states
  const widget = $('ball-widget');
  widget.classList.remove('alert', 'overdue');
  if (state.ballCount % THRESHOLD_STANDARD > THRESHOLD_STANDARD * 0.9) {
    widget.classList.add('alert');
    showAlert(`⚠️ Entretien standard bientôt requis (${formatNum(toStandard)} billes restantes)`);
  }
  if (state.ballCount % THRESHOLD_COMPLETE > THRESHOLD_COMPLETE * 0.95) {
    widget.classList.add('overdue');
  }
}

$('ball-widget').addEventListener('click', () => { $('ball-modal').hidden = false; $('ball-custom').focus(); });
$('bw-edit-btn').addEventListener('click', e => { e.stopPropagation(); $('ball-modal').hidden = false; });

document.querySelectorAll('.ball-add-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    state.ballCount += parseInt(btn.dataset.add);
    updateBallWidget(true);
    saveState();
  });
});

$('ball-save-btn').addEventListener('click', () => {
  const v = parseInt($('ball-custom').value);
  if (!isNaN(v) && v >= 0) { state.ballCount = v; updateBallWidget(true); saveState(); }
  $('ball-modal').hidden = true;
  $('ball-custom').value = '';
});

$('ball-reset-btn').addEventListener('click', () => {
  if (confirm('Remettre le compteur à zéro ?')) {
    state.ballCount = 0; updateBallWidget(true); saveState();
    $('ball-modal').hidden = true;
  }
});

document.querySelectorAll('.modal-close').forEach(btn => {
  btn.addEventListener('click', () => { btn.closest('.modal-overlay').hidden = true; });
});

$('ball-modal').addEventListener('click', e => { if (e.target === $('ball-modal')) $('ball-modal').hidden = true; });
$('ball-custom').addEventListener('keydown', e => { if (e.key === 'Enter') $('ball-save-btn').click(); });
$('alert-dismiss').addEventListener('click', () => { $('alert-banner').hidden = true; });

/* ============================================================
   PARTS SECTION
   ============================================================ */
function renderParts(filter = '') {
  const grid = $('parts-grid');
  if (!grid) return;
  const q = filter.toLowerCase();
  grid.innerHTML = PARTS.map(p => {
    const visible = !q || p.name.toLowerCase().includes(q) || p.ref.toLowerCase().includes(q) || p.desc.toLowerCase().includes(q);
    return `
    <article class="part-card${visible ? '' : ' hidden'}" role="listitem">
      <div class="part-ico" style="background:${p.bg}" aria-hidden="true">
        <svg viewBox="0 0 40 40">${p.icon}</svg>
      </div>
      <div class="part-info">
        <div class="part-name">${p.name}</div>
        <div class="part-ref">${p.ref}</div>
        <div class="part-desc">${p.desc}</div>
        <span class="part-tag tag-${p.tag}">${p.tagLabel}</span>
      </div>
      <div class="part-qty" aria-label="Quantité : ${p.qty}">${p.qty}</div>
    </article>`;
  }).join('');
}

document.addEventListener('input', e => {
  if (e.target.id === 'parts-search') renderParts(e.target.value);
});

/* ============================================================
   DIAGNOSTIC TREE
   ============================================================ */
function renderDiag() {
  state.diagPath = ['root'];
  renderDiagNode();
}

function renderDiagNode() {
  const nodeId = state.diagPath[state.diagPath.length - 1];
  const node = TREE[nodeId];
  const panel = $('diag-panel');
  const result = $('diag-result');

  // Breadcrumb
  renderBreadcrumb();

  if (node.diag) {
    // Show diagnosis
    panel.innerHTML = '';
    result.hidden = false;

    const sev = node.sev;
    const sevMap = { easy: ['sev-easy', '✅ Résolution facile'], medium: ['sev-medium', '⚠️ Résolution modérée'], warning: ['sev-warning', '🔴 Urgent'], info: ['sev-info', 'ℹ️ Info'] };
    const [sevClass, sevLabel] = sevMap[sev] || sevMap.info;
    const partsHtml = node.parts && node.parts.length
      ? `<div class="result-parts"><div class="result-parts-title">Pièces potentiellement requises</div><div class="parts-chips">${node.parts.map(p => `<span class="part-chip">${p}</span>`).join('')}</div></div>` : '';
    const guideBtn = node.fixStep
      ? `<button class="result-guide-btn" data-step="${node.fixStep}">→ Aller à l'étape ${node.fixStep} du guide</button>` : '';

    result.innerHTML = `
    <div class="result-card">
      <div class="result-top">
        <div>
          <div class="result-title">${node.title}</div>
          <div class="result-cause">${node.cause}</div>
        </div>
        <span class="severity-badge ${sevClass}">${sevLabel}</span>
      </div>
      <div class="result-body">
        <div class="result-steps-title">Procédure de résolution</div>
        <ol class="result-steps">${node.steps.map(s => `<li>${s}</li>`).join('')}</ol>
        ${partsHtml}
      </div>
      <div class="result-footer">
        ${guideBtn}
        <button class="result-log-btn" id="result-log">📋 Enregistrer dans le carnet</button>
        <button class="result-restart-btn" id="result-restart">↺ Nouveau diagnostic</button>
      </div>
    </div>`;

    // Bind guide button
    const gb = result.querySelector('.result-guide-btn');
    if (gb) {
      gb.addEventListener('click', () => {
        const sn = parseInt(gb.dataset.step);
        document.querySelector('[data-section="demontage"]').click();
        setTimeout(() => goToStep(sn), 80);
      });
    }

    $('result-log').addEventListener('click', () => {
      logDiagnosticEntry(node);
    });

    $('result-restart').addEventListener('click', () => {
      state.diagPath = ['root'];
      result.hidden = true;
      renderDiagNode();
    });

  } else {
    // Show question
    result.hidden = true;
    panel.style.opacity = '0';
    panel.innerHTML = `
      <div class="diag-question">${node.q}</div>
      <div class="diag-options">
        ${node.opts.map((opt, i) => `
          <button class="diag-option" data-next="${opt.next}" aria-label="${opt.label}" style="animation-delay:${i * 0.05}s">
            <span class="diag-opt-icon" aria-hidden="true">${opt.icon}</span>
            <span class="diag-opt-label">${opt.label}</span>
          </button>`).join('')}
      </div>`;

    requestAnimationFrame(() => {
      panel.style.transition = 'opacity .25s ease, transform .25s ease';
      panel.style.opacity = '1';
    });

    panel.querySelectorAll('.diag-option').forEach(btn => {
      btn.addEventListener('click', () => {
        state.diagPath.push(btn.dataset.next);
        renderDiagNode();
      });
      btn.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); btn.click(); } });
    });
  }
}

function renderBreadcrumb() {
  const bc = $('diag-breadcrumb');
  const labels = { root: 'Accueil', no_fire: 'Ne tire pas', gas_leak: 'Fuite gaz', irregular: 'Tir irrégulier', electric: 'Électronique', noise: 'Bruit', feed: 'Alimentation', spool_jam: 'Clic solénoïde' };
  bc.innerHTML = state.diagPath.map((id, i) => {
    const isLast = i === state.diagPath.length - 1;
    const label = labels[id] || id;
    const sep = i > 0 ? '<span class="bc-sep" aria-hidden="true"> › </span>' : '';
    return `${sep}<span class="bc-item${i === 0 ? ' bc-item--root' : ''}" data-idx="${i}">${label}</span>`;
  }).join('');

  bc.querySelectorAll('.bc-item').forEach(item => {
    const idx = parseInt(item.dataset.idx);
    if (idx < state.diagPath.length - 1) {
      item.addEventListener('click', () => {
        state.diagPath = state.diagPath.slice(0, idx + 1);
        $('diag-result').hidden = true;
        renderDiagNode();
      });
    }
  });
}

function logDiagnosticEntry(node) {
  const entry = {
    id: Date.now(),
    date: today(),
    type: 'reparation',
    notes: `Diagnostic : ${node.title}`,
    fps: null,
    balls: state.ballCount,
  };
  state.maintenanceLog.unshift(entry);
  saveState();
  // Switch to carnet
  document.querySelector('[data-section="carnet"]').click();
  announce('Entrée ajoutée au carnet d\'entretien.');
}

/* ============================================================
   CARNET — FPS
   ============================================================ */
function renderCarnet() {
  renderFpsChart();
  renderFpsStats();
  renderLog();
  $('log-balls').value = formatNum(state.ballCount);
}

$('btn-add-fps').addEventListener('click', () => {
  $('fps-form').hidden = false;
  $('fps-value').focus();
});
$('fps-cancel').addEventListener('click', () => { $('fps-form').hidden = true; });
$('fps-save').addEventListener('click', () => {
  const fps = parseFloat($('fps-value').value);
  if (isNaN(fps) || fps < 50 || fps > 450) { announce('Valeur FPS invalide (50–450)'); return; }
  const entry = { date: today(), fps, temp: parseFloat($('fps-temp').value) || null, balls: state.ballCount };
  state.fpsHistory.push(entry);
  if (state.fpsHistory.length > 30) state.fpsHistory.shift();
  saveState();
  $('fps-form').hidden = true;
  $('fps-value').value = '';
  $('fps-temp').value = '';
  renderFpsChart();
  renderFpsStats();
  if (fps > 300) showAlert('⚠️ FPS > 300 — Réduisez la vélocité avant de jouer !');
  announce(`Mesure ${fps} FPS enregistrée.`);
});

function renderFpsChart() {
  const svg = $('fps-chart');
  if (!svg) return;
  const data = state.fpsHistory;

  if (data.length < 2) {
    svg.innerHTML = `<text x="300" y="65" font-family="sans-serif" font-size="12" fill="#3a4260" text-anchor="middle">Ajoutez des mesures pour voir l'historique</text>`;
    return;
  }

  const W = 600, H = 120, pad = { t: 10, r: 20, b: 30, l: 45 };
  const vals = data.map(d => d.fps);
  const minV = Math.min(...vals, 250), maxV = Math.max(...vals, 310);
  const range = maxV - minV || 1;
  const iw = W - pad.l - pad.r, ih = H - pad.t - pad.b;

  const px = (i) => pad.l + (i / (data.length - 1)) * iw;
  const py = (v) => H - pad.b - ((v - minV) / range) * ih;

  // Grid lines
  let grid = '';
  const ticks = [260, 280, 300];
  ticks.forEach(t => {
    if (t >= minV && t <= maxV) {
      const y = py(t);
      const color = t === 300 ? '#e63946' : '#1e2340';
      grid += `<line x1="${pad.l}" y1="${y}" x2="${W - pad.r}" y2="${y}" stroke="${color}" stroke-width="${t === 300 ? 1.5 : 1}" stroke-dasharray="${t === 300 ? '4,3' : '3,3'}"/>`;
      grid += `<text x="${pad.l - 5}" y="${y + 4}" font-family="monospace" font-size="9" fill="${t === 300 ? '#e63946' : '#3a4260'}" text-anchor="end">${t}</text>`;
    }
  });
  if (ticks.indexOf(300) === -1 || (maxV >= 300 && minV <= 300)) {
    const y300 = py(300);
    grid += `<line x1="${pad.l}" y1="${y300}" x2="${W - pad.r}" y2="${y300}" stroke="#e63946" stroke-width="1.5" stroke-dasharray="4,3" opacity=".6"/>`;
    grid += `<text x="${pad.l - 5}" y="${y300 + 4}" font-family="monospace" font-size="9" fill="#e63946" text-anchor="end">300</text>`;
  }

  // Area fill
  const pts = data.map((d, i) => `${px(i)},${py(d.fps)}`).join(' ');
  const areaPath = `M${px(0)},${py(data[0].fps)} ` + data.slice(1).map((d, i) => `L${px(i + 1)},${py(d.fps)}`).join(' ') + ` L${px(data.length - 1)},${H - pad.b} L${px(0)},${H - pad.b} Z`;

  // Line
  const linePath = `M${px(0)},${py(data[0].fps)} ` + data.slice(1).map((d, i) => `L${px(i + 1)},${py(d.fps)}`).join(' ');

  // Dots
  const dots = data.map((d, i) => {
    const over = d.fps > 300;
    return `<circle cx="${px(i)}" cy="${py(d.fps)}" r="4" fill="${over ? '#e63946' : '#457b9d'}" stroke="${over ? '#ff8b94' : '#74b3ce'}" stroke-width="1.5">
      <title>${d.fps} FPS – ${d.date}</title></circle>`;
  }).join('');

  svg.innerHTML = `
    <defs>
      <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#457b9d" stop-opacity=".25"/>
        <stop offset="100%" stop-color="#457b9d" stop-opacity="0"/>
      </linearGradient>
    </defs>
    ${grid}
    <path d="${areaPath}" fill="url(#areaGrad)"/>
    <path d="${linePath}" fill="none" stroke="#457b9d" stroke-width="2" stroke-linejoin="round"/>
    ${dots}
    <text x="${pad.l}" y="${H - 5}" font-family="sans-serif" font-size="8" fill="#3a4260">${data[0].date}</text>
    <text x="${W - pad.r}" y="${H - 5}" font-family="sans-serif" font-size="8" fill="#3a4260" text-anchor="end">${data[data.length - 1].date}</text>
  `;
}

function renderFpsStats() {
  const el = $('fps-stats');
  if (!el) return;
  const data = state.fpsHistory;
  if (data.length === 0) { el.innerHTML = ''; return; }
  const vals = data.map(d => d.fps);
  const avg = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
  const last = vals[vals.length - 1];
  const mx = Math.max(...vals), mn = Math.min(...vals);
  el.innerHTML = `
    <div class="fps-stat"><span class="fps-stat-n">${last}</span><span class="fps-stat-l">Dernier</span></div>
    <div class="fps-stat"><span class="fps-stat-n">${avg}</span><span class="fps-stat-l">Moyenne</span></div>
    <div class="fps-stat"><span class="fps-stat-n">${mn}–${mx}</span><span class="fps-stat-l">Plage</span></div>
    <div class="fps-stat"><span class="fps-stat-n">${data.length}</span><span class="fps-stat-l">Mesures</span></div>
  `;
}

/* ============================================================
   CARNET — LOG
   ============================================================ */
$('btn-add-log').addEventListener('click', () => {
  $('log-form').hidden = false;
  $('log-balls').value = formatNum(state.ballCount);
  $('log-type').focus();
});
$('log-cancel').addEventListener('click', () => { $('log-form').hidden = true; });
$('log-save').addEventListener('click', () => {
  const entry = {
    id: Date.now(),
    date: today(),
    type: $('log-type').value,
    notes: $('log-notes').value.trim(),
    fps: parseFloat($('log-fps').value) || null,
    balls: state.ballCount,
  };
  state.maintenanceLog.unshift(entry);
  if (state.maintenanceLog.length > 50) state.maintenanceLog.pop();
  saveState();
  $('log-form').hidden = true;
  $('log-notes').value = '';
  $('log-fps').value = '';
  renderLog();
  announce('Entrée enregistrée dans le carnet.');
});

function renderLog() {
  const list = $('log-list');
  if (!list) return;
  if (state.maintenanceLog.length === 0) {
    list.innerHTML = '<div class="log-empty"><span class="log-empty-icon">📋</span>Aucune entrée — ajoutez votre premier entretien.</div>';
    return;
  }
  const typeIcons = { 'after-game': '🎯', standard: '🔧', complete: '⚙️', reparation: '🛠️', reglage: '📏' };
  const typeLabels = { 'after-game': 'Après partie', standard: 'Standard', complete: 'Complet', reparation: 'Réparation', reglage: 'Réglage' };
  list.innerHTML = state.maintenanceLog.map(e => `
    <div class="log-entry" data-id="${e.id}" role="listitem">
      <span class="log-entry-icon" aria-hidden="true">${typeIcons[e.type] || '🔧'}</span>
      <div class="log-entry-body">
        <div class="log-entry-top">
          <span class="log-entry-type log-type-${e.type}">${typeLabels[e.type] || e.type}</span>
          <span class="log-entry-date">${e.date}</span>
          ${e.fps ? `<span class="log-entry-fps">${e.fps} FPS</span>` : ''}
        </div>
        ${e.notes ? `<div class="log-entry-notes">${e.notes}</div>` : ''}
        ${e.balls != null ? `<div class="log-entry-balls">Compteur : ${formatNum(e.balls)} billes</div>` : ''}
      </div>
      <button class="log-delete" data-id="${e.id}" aria-label="Supprimer cette entrée">🗑️</button>
    </div>`).join('');

  list.querySelectorAll('.log-delete').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = parseInt(btn.dataset.id);
      state.maintenanceLog = state.maintenanceLog.filter(e => e.id !== id);
      saveState(); renderLog();
    });
  });
}

/* ============================================================
   KEYBOARD SHORTCUTS
   ============================================================ */
document.addEventListener('keydown', e => {
  const active = document.querySelector('.guide-section.active');
  if (!active || active.id !== 'section-demontage') return;
  const tag = document.activeElement.tagName;
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) return;
  switch(e.key) {
    case 'ArrowRight': case 'ArrowDown': e.preventDefault(); goToStep(state.currentStep + 1); break;
    case 'ArrowLeft':  case 'ArrowUp':   e.preventDefault(); goToStep(state.currentStep - 1); break;
    case ' ': e.preventDefault(); if (state.isPlaying) stopPlay(); else startPlay(); break;
    case '1': case '2': case '3': case '4': case '5': case '6': case '7': case '8':
      goToStep(parseInt(e.key)); break;
  }
});

/* ============================================================
   INTERSECTION OBSERVER — scroll animations
   ============================================================ */
function initScrollAnim() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.step-card, .part-card, .fps-panel, .log-panel').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity .4s ease, transform .4s ease';
    io.observe(el);
  });
}

/* ============================================================
   INIT
   ============================================================ */
function init() {
  loadState();

  // Restore notes
  Object.entries(state.notes).forEach(([n, txt]) => {
    const ta = $(`note-${n}`);
    if (ta) ta.value = txt;
  });

  // Restore completed steps
  state.completedSteps.forEach(n => {
    const card = document.querySelector(`.step-card[data-step="${n}"]`);
    if (card) card.classList.add('completed');
  });

  // Init guide
  $('total-steps').textContent = TOTAL_STEPS;
  $('stat-done').textContent = state.completedSteps.size;
  goToStep(1);
  updateBallWidget();

  // Render parts immediately (hidden until tab shown)
  renderParts();

  // Scroll animations
  initScrollAnim();

  // Parts search
  const ps = $('parts-search');
  if (ps) ps.addEventListener('input', () => renderParts(ps.value));
}

document.addEventListener('DOMContentLoaded', init);
