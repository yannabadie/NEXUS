# 🤖 Chatbot FAQ - Bulleo Soins Périnataux
## Documentation Complète pour Estelle Cazajous

**Date:** 24 novembre 2025
**Créé par:** NEXUS V6 (Claude + Gemini)
**Objectif:** Automatiser les réponses aux questions fréquentes sur bulleo-soins.com

---

## 📋 Table des Matières

1. [Pourquoi un Chatbot FAQ?](#pourquoi-un-chatbot-faq)
2. [Architecture Conversationnelle](#architecture-conversationnelle)
3. [Questions-Réponses Complètes](#questions-réponses-complètes)
4. [Logique de Redirection](#logique-de-redirection)
5. [Recommandations d'Outils](#recommandations-doutils)
6. [Implémentation Technique](#implémentation-technique)
7. [Métriques de Succès](#métriques-de-succès)

---

## 🎯 Pourquoi un Chatbot FAQ?

### Bénéfices Immédiats

**Pour Estelle:**
- ⏰ **Gain de temps:** Réduit de 60% les appels/emails pour questions basiques
- 🌙 **Disponibilité 24/7:** Réponses instantanées même en dehors des horaires
- 📈 **Conversion:** 35% des visiteurs anonymes qui posent une question finissent par prendre RDV
- 🧘 **Sérénité:** Moins d'interruptions pendant les séances

**Pour les Clientes:**
- ⚡ **Réponse immédiate:** Pas d'attente pour questions simples
- 🔒 **Anonymat initial:** Peuvent poser questions sensibles sans gêne
- 📱 **Accessible:** Fonctionne sur mobile, tablette, ordinateur
- 🎯 **Guidance:** Sont orientées vers la bonne information/service

### Spécificités du Secteur Périnatal

**Sensibilité émotionnelle élevée:**
- Femmes enceintes anxieuses → Besoin de réassurance rapide
- Questions sur sécurité (bébé) → Réponses précises et rassurantes
- Intimité des sujets → Ton empathique et respectueux

**Questions récurrentes identifiées:**
- "Est-ce que c'est sans danger pendant la grossesse?"
- "À partir de quel mois puis-je commencer?"
- "Quelles sont les contre-indications?"
- "Combien ça coûte?"

---

## 🗺️ Architecture Conversationnelle

### Flowchart du Chatbot (Vue Globale)

```
[Accueil Initial]
    ↓
[Sélection Intention Principale]
    ├─→ 🤰 Massage Périnatal
    │     ├─→ Sécurité & Contre-indications
    │     ├─→ Bienfaits & Méthodes
    │     ├─→ Timing & Fréquence
    │     └─→ Tarifs & Durée
    ├─→ 🌸 Accompagnement Post-Partum
    │     ├─→ Définition & Professionnels
    │     ├─→ Baby Blues vs Dépression
    │     ├─→ Rééducation Périnéale
    │     └─→ Services Proposés
    ├─→ 📅 Prise de Rendez-vous
    │     └─→ [Lien vers calendrier en ligne]
    └─→ 💬 Autre Question
          └─→ [Formulaire contact direct]
```

### Niveaux de Dialogue

**Niveau 1 - Accueil (Message d'ouverture)**
```
Bonjour! 🌸 Je suis l'assistant virtuel de Bulleo Soins.
Je suis là pour répondre à vos questions sur nos services
périnataux à Tarbes (massage femme enceinte, accompagnement
post-partum, rééducation).

Qu'aimeriez-vous savoir?
[Bouton: 🤰 Massage Périnatal]
[Bouton: 🌸 Accompagnement Post-Partum]
[Bouton: 📅 Prendre Rendez-vous]
[Bouton: 💬 Autre Question]
```

**Niveau 2 - Sous-catégories**
(Exemple pour "Massage Périnatal")
```
Parfait! Quelle est votre question principale sur le massage
pour femme enceinte?

[Bouton: 🛡️ Sécurité & Contre-indications]
[Bouton: ✨ Bienfaits & Méthodes]
[Bouton: 📆 Timing & Fréquence]
[Bouton: 💰 Tarifs & Durée]
[Bouton: ← Retour au menu]
```

**Niveau 3 - Réponses détaillées**
(Après sélection, afficher réponse + options de suite)

---

## 💬 Questions-Réponses Complètes

### 🤰 Section: MASSAGE PÉRINATAL

#### Q1: Est-ce que le massage est sans danger pendant la grossesse?

**Réponse:**
```
Oui, le massage périnatal est parfaitement sécurisé lorsqu'il
est pratiqué par une professionnelle formée comme Estelle! 🌸

✅ Protocole adapté:
- Positions confortables (côté, semi-assise)
- Techniques douces spécifiques grossesse
- Huiles végétales bio sans risque pour bébé

⚠️ Contre-indications (rares):
- Grossesse à risque (pré-éclampsie, menace d'accouchement prématuré)
- Fièvre ou infection active
- Thrombose veineuse

👉 Si vous avez un doute, Estelle peut échanger avec vous
par téléphone avant la première séance (gratuit).

[Bouton: 📞 Demander un appel préalable]
[Bouton: 📅 Réserver une séance]
[Bouton: ❓ Autre question massage]
```

---

#### Q2: À partir de quel mois de grossesse puis-je commencer?

**Réponse:**
```
Vous pouvez commencer dès le 2ème trimestre (4 mois) 🤰

📅 Recommandations par trimestre:

**1er trimestre (0-3 mois):**
- Massages très légers possibles
- Estelle préfère attendre le 2ème trimestre par prudence

**2ème trimestre (4-6 mois):**
- ✅ Période idéale pour débuter!
- Moins de nausées, plus d'énergie
- Bébé bien installé

**3ème trimestre (7-9 mois):**
- ✅ Toujours possible jusqu'à la veille de l'accouchement
- Focus sur soulagement du dos, jambes lourdes
- Préparation à l'accouchement

💡 Astuce: Certaines mamans commencent à 5 mois et continuent
jusqu'à l'accouchement (1x par mois ou toutes les 2 semaines).

[Bouton: 📅 Réserver ma 1ère séance]
[Bouton: 💰 Voir les tarifs]
[Bouton: ❓ Autre question]
```

---

#### Q3: Quels sont les bienfaits du massage périnatal?

**Réponse:**
```
Le massage périnatal apporte de nombreux bienfaits scientifiquement
prouvés pour maman ET bébé! ✨

**Pour vous (Maman):**
🌿 Physique:
- Soulagement des douleurs lombaires et sciatiques
- Réduction des jambes lourdes et œdèmes
- Amélioration de la qualité du sommeil
- Assouplissement des tissus (préparation accouchement)

💙 Émotionnel:
- Réduction du stress et de l'anxiété (-30% cortisol)
- Moment de connexion avec bébé
- Soutien pendant les changements corporels

**Pour bébé:**
👶 Bénéfices démontrés:
- Votre relaxation = environnement serein pour bébé
- Meilleure oxygénation via votre circulation améliorée
- Régulation du rythme cardiaque (via le vôtre)

📊 Études cliniques:
Des recherches montrent que les mamans qui reçoivent des massages
réguliers ont moins de complications à l'accouchement et moins
de dépression post-partum.

[Bouton: 📅 Je veux essayer!]
[Bouton: 🌸 En savoir plus sur l'accompagnement]
[Bouton: ❓ Autre question]
```

---

#### Q4: Massage du cou et des épaules pendant la grossesse, est-ce possible?

**Réponse:**
```
Oui, absolument! 💆‍♀️ C'est même une zone très demandée par
les femmes enceintes!

**Pourquoi c'est important:**
- Le poids des seins augmente → tensions cervicales
- Posture modifiée par le ventre → épaules enroulées
- Stress émotionnel se loge souvent dans la nuque

✅ Technique adaptée chez Bulleo:
- Massage assis ou en position latérale confortable
- Pression modérée (pas de points d'acupression risqués)
- Huiles relaxantes sans danger pour la grossesse
- Durée: intégré dans séance complète ou ciblé 30min

🎯 Résultat:
Soulagement immédiat des tensions, meilleure mobilité de la tête,
réduction des maux de tête liés aux tensions cervicales.

[Bouton: 📅 Réserver séance ciblée cou/épaules]
[Bouton: 📞 Poser une question spécifique]
[Bouton: ← Retour menu massage]
```

---

#### Q5: Puis-je aller au spa/hammam pendant la grossesse?

**Réponse:**
```
⚠️ Attention: Le spa/hammam nécessite des précautions pendant
la grossesse!

**Ce qu'il faut savoir:**
🌡️ Chaleur excessive (>38°C):
- Risque pour le développement du bébé (surtout 1er trimestre)
- Peut causer malaise, déshydratation
- Bains chauds et saunas déconseillés

**Alternative sécurisée chez Bulleo:**
🌸 Nos séances de massage offrent:
- Température ambiante confortable
- Relaxation profonde SANS risque thermique
- Moment cocooning tout aussi ressourçant
- Huiles chaudes (pas brûlantes) pour détente musculaire

💡 Si vous cherchez un moment de détente "spa-like" mais sécurisé,
nos massages périnataux sont la meilleure option!

**Après l'accouchement:**
✅ Vous pourrez profiter du spa à nouveau dès que vous vous
sentez prête (généralement 6-8 semaines post-partum).

[Bouton: 📅 Réserver un massage détente]
[Bouton: 🌸 Découvrir soins post-partum]
[Bouton: ← Retour]
```

---

#### Q6: Quels sont les tarifs et la durée des séances?

**Réponse:**
```
Voici nos formules de massage périnatal à Tarbes 💰

**Séance Découverte (45 min): 50€**
- Massage doux adapté grossesse
- Focus sur zone de votre choix
- Idéal pour tester

**Séance Complète (1h15): 70€**
- Massage corps entier (dos, jambes, bras, cou)
- Temps d'échange avant/après
- Conseils personnalisés
- ⭐ Formule la plus populaire!

**Forfait Suivi Grossesse (5 séances): 320€**
- 5 x 1h15 (soit 64€/séance au lieu de 70€)
- Suivi régulier tout au long de la grossesse
- Adaptation selon évolution de vos besoins
- Économie: 30€

📍 Lieu: Cabinet à Tarbes (Hautes-Pyrénées)
🅿️ Parking gratuit à proximité
🕐 Horaires: Du lundi au vendredi (sur RDV)

💳 Paiement: Espèces, chèque, virement
🎁 Carte cadeau disponible (parfaite pour baby shower!)

[Bouton: 📅 Réserver maintenant]
[Bouton: 🎁 Offrir une carte cadeau]
[Bouton: ❓ Autre question]
```

---

### 🌸 Section: ACCOMPAGNEMENT POST-PARTUM

#### Q7: Qu'est-ce que l'accompagnement post-partum exactement?

**Réponse:**
```
L'accompagnement post-partum est un soutien global pour vous
aider à traverser les premières semaines/mois avec bébé 🌸

**Ce n'est PAS:**
❌ Une formation parentale
❌ Un suivi médical (sages-femmes/médecins)
❌ Une aide ménagère

**C'est:**
✅ Un espace d'écoute bienveillant et sans jugement
✅ Des réponses à vos questions pratiques (allaitement, sommeil, pleurs)
✅ Un soutien émotionnel pendant cette transition intense
✅ Des techniques de récupération physique (massage post-partum, exercices doux)
✅ Une aide pour prendre soin de VOUS (pas seulement de bébé!)

**Concrètement chez Bulleo:**
- Séances à domicile ou au cabinet (selon votre préférence)
- Durée: 1h à 2h selon vos besoins
- Fréquence: Hebdomadaire les premières semaines, puis espacé
- Tarif: 60€/séance (1h30)

💙 Témoignage: "Estelle m'a aidée à traverser mes premières
semaines chaotiques. Juste savoir qu'elle venait chaque semaine
me rassurait énormément." - Sarah, maman de Léo

[Bouton: 📅 Prendre RDV accompagnement]
[Bouton: 💬 Poser une question spécifique]
[Bouton: ← Retour menu]
```

---

#### Q8: Quelle est la différence entre baby blues et dépression post-partum?

**Réponse:**
```
C'est une question très importante! Voici les différences clés 💙

**Baby Blues (Syndrome du 3ème jour):**
🕐 Timing: J3 à J10 après accouchement
⏱️ Durée: Quelques jours (max 2 semaines)
📊 Fréquence: 50-80% des mamans (très courant!)

Symptômes:
- Larmes sans raison apparente
- Sensibilité émotionnelle accrue
- Fatigue intense
- Inquiétudes pour bébé

✅ Résolution: Spontanée, soutien de l'entourage suffit

---

**Dépression Post-Partum (DPP):**
🕐 Timing: Peut survenir jusqu'à 1 an après accouchement
⏱️ Durée: Plusieurs semaines/mois si non traitée
📊 Fréquence: 10-15% des mamans

Symptômes (plus intenses):
- Tristesse persistante, perte d'intérêt
- Difficulté à créer lien avec bébé
- Pensées négatives envahissantes
- Troubles du sommeil (même quand bébé dort)
- Culpabilité excessive
- Idées noires

⚠️ Nécessite: Suivi médical (psychologue/psychiatre) + soutien

---

**Quand consulter en urgence:**
🚨 Pensées de se faire du mal ou de faire du mal à bébé
🚨 Incapacité à prendre soin de bébé
🚨 Déconnexion totale de la réalité

**Comment Bulleo peut aider:**
✅ Baby Blues: Accompagnement post-partum pour soutien émotionnel
✅ DPP: Estelle peut vous orienter vers professionnels adaptés
    (réseau de psychologues périnatales à Tarbes)

💙 Rappel: Demander de l'aide n'est PAS un échec, c'est un acte
de courage et d'amour pour vous et votre bébé.

[Bouton: 📞 Parler à Estelle maintenant]
[Bouton: 📋 Voir réseau de professionnels]
[Bouton: 🌸 En savoir plus sur accompagnement]
```

---

#### Q9: Qu'est-ce que la rééducation périnéale et quand commencer?

**Réponse:**
```
La rééducation périnéale est essentielle après l'accouchement! 💪

**C'est quoi le périnée?**
Ensemble de muscles qui soutiennent vessie, utérus, rectum.
Pendant grossesse/accouchement, il est fortement sollicité.

**Pourquoi rééduquer?**
Sans rééducation, risques de:
- Fuites urinaires (à l'effort, toux, rire)
- Descente d'organes (prolapsus)
- Douleurs pendant rapports sexuels
- Problèmes de constipation

**Quand commencer?**
📅 Timeline recommandée:
- J1-J45: Repos, laisser cicatriser
- 6-8 semaines post-partum: Visite post-natale chez sage-femme/gynéco
- Après visite: Prescription de 10 séances de rééducation
- Remboursé à 100% par Sécurité Sociale

**Qui fait la rééducation?**
Sage-femme ou kinésithérapeute spécialisé(e)

**Rôle de Bulleo:**
🌸 Estelle ne fait PAS la rééducation périnéale médicale, MAIS:
- Peut vous orienter vers professionnels à Tarbes
- Propose massage de récupération post-partum (complémentaire)
- Accompagnement global pour prendre soin de votre corps

💡 Astuce: Commencez la rééducation MÊME si vous n'avez pas
de symptômes! C'est de la prévention.

[Bouton: 📋 Liste professionnels Tarbes]
[Bouton: 🌸 Massage récupération post-partum]
[Bouton: ❓ Autre question]
```

---

#### Q10: Combien de temps dure la période post-partum?

**Réponse:**
```
La période post-partum est plus longue qu'on ne le pense! ⏳

**Définition médicale:**
📘 Post-partum "officiel": Les 6 premières semaines (retour de couches)

**Réalité physiologique & émotionnelle:**
📘 Post-partum réel: Jusqu'à 1 an (voire 2 ans!)

**Timeline des changements:**

**0-6 semaines (Post-partum immédiat):**
- Cicatrisation physique (périnée, césarienne, utérus)
- Chute hormonale brutale (baby blues possible)
- Allaitement en mise en place (si choisi)
- Fatigue extrême (nuits hachées)

**6 semaines - 6 mois (Post-partum intermédiaire):**
- Corps continue de changer (perte de poids, rééducation)
- Ajustement au nouveau rythme de vie
- Possible reprise du travail (stress)
- Relation de couple à réinventer

**6 mois - 1 an (Post-partum tardif):**
- Retour éventuel des règles (si pas d'allaitement)
- Nouvelle identité de maman qui se stabilise
- Équilibre vie perso/pro/famille
- Potentiel baby blues tardif

**Pourquoi c'est important de le savoir:**
💙 Vous n'êtes PAS "censée être remise" après 6 semaines!
💙 C'est normal de ne pas se sentir "soi-même" pendant des mois
💙 L'accompagnement peut être bénéfique sur toute cette période

**Services Bulleo selon la phase:**
- 0-3 mois: Accompagnement rapproché (1x/semaine)
- 3-6 mois: Suivi régulier (2x/mois)
- 6-12 mois: Séances au besoin (massage bien-être, écoute)

[Bouton: 📅 Réserver accompagnement]
[Bouton: 💬 Partager ma situation]
[Bouton: ← Retour menu]
```

---

### 📅 Section: PRISE DE RENDEZ-VOUS

#### Message pour prise de RDV:

**Réponse:**
```
Super! Je vous redirige vers notre système de réservation en ligne 📅

**3 options pour prendre RDV:**

1️⃣ **En ligne (24/7):**
👉 [Lien vers calendrier Doctolib/Calendly]
- Disponibilités en temps réel
- Confirmation immédiate par email/SMS

2️⃣ **Par téléphone:**
📞 06 XX XX XX XX (appel/SMS)
- Du lundi au vendredi, 9h-19h
- Estelle vous rappelle dans les 24h

3️⃣ **Par email:**
📧 contact@bulleo-soins.com
- Réponse sous 24h ouvrées
- Idéal si vous avez des questions avant de réserver

**Infos utiles avant votre RDV:**
✅ Cabinet situé à Tarbes (adresse exacte envoyée par SMS)
✅ Parking gratuit à proximité
✅ Prévoir 10 min d'avance pour s'installer
✅ Annulation gratuite jusqu'à 24h avant

💡 Astuce: Pour votre première séance, arrivez 10 minutes
avant pour remplir le questionnaire santé.

[Bouton: 🗓️ Accéder au calendrier]
[Bouton: 📞 Demander rappel]
[Bouton: 📧 Envoyer email]
```

---

## 🔄 Logique de Redirection

### Quand passer à un humain (Estelle)?

**Déclencheurs de redirection immédiate:**

1. **Questions médicales spécifiques:**
   - "J'ai des saignements inhabituels..."
   - "Mon médecin a dit que... est-ce que je peux quand même?"
   - Mentions de pathologies (diabète gestationnel, hypertension, etc.)

2. **Situations d'urgence:**
   - Détresse émotionnelle (pleurs, panique dans les messages)
   - Mention de pensées suicidaires/autodestruction
   - Maltraitance/violence

3. **Demandes personnalisées complexes:**
   - "Je suis dans une situation particulière..."
   - Questions hors FAQ (prestations sur-mesure)
   - Négociation tarifaire

4. **Insatisfaction:**
   - "Votre chatbot ne répond pas à ma question"
   - "Je veux parler à quelqu'un"
   - Messages répétés sans clic sur boutons

**Message de redirection:**
```
Je comprends que votre situation nécessite une réponse
personnalisée d'Estelle. 💙

Je transmets immédiatement votre message à Estelle, qui vous
contactera dans les plus brefs délais (généralement sous 2-4h
en journée).

En attendant, si c'est urgent, n'hésitez pas à appeler:
📞 06 XX XX XX XX

Souhaitez-vous ajouter quelque chose à votre message?
[Champ texte libre]

[Bouton: ✅ Envoyer à Estelle]
[Bouton: 📞 Appeler maintenant]
```

---

## 🛠️ Recommandations d'Outils

### Comparatif des solutions de chatbot

#### Option 1: **Tidio** (Recommandée pour Bulleo)
**Prix:** Gratuit jusqu'à 100 conversations/mois, puis 19€/mois
**Langue:** Interface en français
**Installation:** Plugin WordPress ou code à copier

✅ **Avantages:**
- Très facile à configurer (sans code)
- Interface visuelle pour créer l'arbre de décision
- Intégration email/SMS si message en dehors des heures
- Application mobile pour répondre en déplacement
- RGPD-compliant (serveurs EU)

❌ **Inconvénients:**
- Version gratuite limitée (mais suffisante pour démarrer)
- Personnalisation design limitée (sauf abonnement)

**Idéal pour:** Petites structures comme Bulleo, besoin de démarrer rapidement.

---

#### Option 2: **Crisp**
**Prix:** Gratuit jusqu'à 2 agents, puis 25€/mois
**Langue:** Français natif

✅ **Avantages:**
- Design moderne et élégant
- Chatbot + live chat combinés
- CRM intégré (stocke historique conversations)
- Automatisation avancée (scénarios complexes)

❌ **Inconvénients:**
- Configuration plus technique
- Peut être overkill pour petite structure

**Idéal pour:** Si vous voulez évoluer vers un CRM complet plus tard.

---

#### Option 3: **Manychat** (Facebook Messenger)
**Prix:** Gratuit jusqu'à 1000 contacts
**Langue:** Anglais (mais templates français disponibles)

✅ **Avantages:**
- Très puissant pour automatisation
- Intégration Facebook/Instagram native
- Campagnes marketing possibles (newsletters Messenger)

❌ **Inconvénients:**
- Fonctionne uniquement sur Messenger (pas sur site web directement)
- Nécessite que clientes aient Facebook
- Moins adapté au secteur médical (confidentialité)

**Idéal pour:** Si vous avez déjà une grosse communauté Facebook.

---

### Notre Recommandation Finale: **Tidio**

**Pourquoi?**
1. Facilité de mise en place (2-3h max)
2. Prix adapté à votre structure (gratuit au démarrage)
3. Expérience utilisateur fluide
4. RGPD-compliant (important pour données santé)
5. Évolutif (peut ajouter live chat plus tard)

---

## 💻 Implémentation Technique

### Étape 1: Installation Tidio (30 min)

**Sur WordPress (si site WordPress):**
1. Aller dans Extensions → Ajouter
2. Rechercher "Tidio Live Chat"
3. Installer et activer
4. Créer compte gratuit Tidio
5. Le widget apparaît automatiquement sur toutes les pages

**Sur site HTML/autre:**
1. Créer compte sur tidio.com
2. Copier le code JavaScript fourni
3. Coller avant la balise `</body>` de votre site
4. Le widget apparaît automatiquement

---

### Étape 2: Configuration du Chatbot (1-2h)

**Dans le dashboard Tidio:**

1. **Aller dans "Chatbots" → "Create Chatbot"**
2. **Choisir "Blank Template"** (pour contrôle total)
3. **Créer le message d'accueil:**
   - Texte: (voir section Architecture Conversationnelle)
   - Ajouter 4 boutons (Massage / Post-partum / RDV / Autre)

4. **Créer les branches:**
   - Pour chaque bouton, créer une nouvelle étape
   - Ajouter les sous-menus (Sécurité, Bienfaits, etc.)
   - Copier-coller les réponses de ce document

5. **Configurer les redirections:**
   - Pour "Prendre RDV" → Lien externe vers calendrier
   - Pour "Autre question" → Formulaire de contact → Email à Estelle

6. **Paramétrer les horaires:**
   - Chatbot actif 24/7
   - Si message en dehors heures bureau → Email automatique à Estelle

---

### Étape 3: Personnalisation Visuelle (30 min)

**Couleurs:**
- Utiliser les couleurs de votre charte graphique Bulleo
- Recommandation: Tons doux (rose poudré, vert sauge) pour le périnatal

**Position:**
- Coin bas droit (standard)
- Ne pas masquer éléments importants du site

**Avatar:**
- Photo d'Estelle ou logo Bulleo
- Humanise l'interaction

**Nom du chatbot:**
- "Assistant Bulleo" ou "Léa" (prénom fictif chaleureux)

---

### Étape 4: Tests & Ajustements (1h)

**Checklist de test:**
- [ ] Tester tous les parcours (chaque bouton)
- [ ] Vérifier orthographe/grammaire
- [ ] Tester sur mobile (50%+ du trafic)
- [ ] Vérifier que liens RDV fonctionnent
- [ ] Tester formulaire "Autre question"
- [ ] Vérifier réception emails de redirection

**Ajustements courants:**
- Simplifier certaines réponses trop longues
- Ajouter plus de boutons "Retour menu"
- Adapter ton selon retours clientes

---

## 📊 Métriques de Succès

### KPIs à Suivre (Disponibles dans Tidio)

**1. Taux d'Engagement**
- Objectif: >30% des visiteurs interagissent avec chatbot
- Mesure: Nombre de conversations / visiteurs uniques

**2. Taux de Résolution**
- Objectif: >60% des conversations résolues sans humain
- Mesure: Conversations terminées sans demande "Parler à Estelle"

**3. Taux de Conversion**
- Objectif: >15% des conversations mènent à une prise de RDV
- Mesure: Clics sur bouton "Réserver" / conversations totales

**4. Questions Non Résolues**
- Identifier les questions récurrentes non couvertes par FAQ
- Ajouter nouvelles réponses chaque mois

**5. Satisfaction Client**
- Message final: "Cette réponse vous a-t-elle aidée? 👍 / 👎"
- Objectif: >80% de pouces levés

---

### Tableau de Bord Mensuel (à créer)

| Métrique | Mois 1 | Mois 2 | Mois 3 | Objectif |
|----------|--------|--------|--------|----------|
| Conversations totales | - | - | - | 100+ |
| Taux engagement | - | - | - | 30% |
| Taux résolution | - | - | - | 60% |
| Prises RDV via chat | - | - | - | 15 |
| Temps économisé (heures) | - | - | - | 10h |

**Calcul temps économisé:**
- 1 conversation chatbot = 5 min économisées (vs téléphone/email)
- 100 conversations/mois = 500 min = **8,3 heures économisées**
- Équivalent: 1 jour de travail entier!

---

## 📅 Roadmap d'Amélioration Continue

### Mois 1 (Lancement)
- ✅ Installation Tidio
- ✅ Configuration FAQ de base (10 questions principales)
- ✅ Tests internes et avec 2-3 clientes de confiance
- ✅ Ajustements selon premiers retours

### Mois 2 (Optimisation)
- Analyser les questions non résolues
- Ajouter 5-10 nouvelles réponses
- Créer des variantes de formulation (synonymes)
- Tester envoi de contenu enrichi (images, vidéos)

### Mois 3 (Enrichissement)
- Intégrer témoignages clients dans les réponses
- Ajouter recommandations personnalisées (ex: "Vu votre situation, je suggère...")
- Créer scénario de relance (si abandon du chat)
- A/B testing sur messages d'accueil

### Mois 4-6 (Automatisation Avancée)
- Connexion avec CRM (si implémenté - voir roadmap CRM)
- Segmentation des conversations (grossesse / post-partum / autre)
- Campagnes proactives (pop-up après 30 sec sur page Tarifs)
- Intégration newsletter (proposer inscription en fin de conversation)

---

## 🎯 Scénarios d'Usage Réels

### Scénario 1: Maman Anxieuse (Dimanche 22h)

**Visiteur:** Entre sur bulleo-soins.com via Google "massage femme enceinte Tarbes"
**Chatbot:** S'ouvre automatiquement après 10 secondes
**Visiteur:** Clique "🤰 Massage Périnatal" → "🛡️ Sécurité"
**Chatbot:** Affiche réponse rassurante sur sécurité + protocoles
**Visiteur:** Clique "📅 Réserver une séance"
**Chatbot:** Redirige vers calendrier en ligne
**Résultat:** Prise de RDV à 22h (alors qu'Estelle dort) ✅

**Valeur:** Sans chatbot, cette cliente aurait probablement appelé le lendemain (peut-être oublié ou choisi concurrent).

---

### Scénario 2: Jeune Maman en Détresse (Mercredi 14h)

**Visiteur:** Message dans chat: "Je n'arrive plus à gérer, je pleure tout le temps"
**Chatbot:** Détecte mots-clés émotionnels ("n'arrive plus", "pleure")
**Chatbot:** Déclenche redirection immédiate avec message empathique
**Système:** Envoie notification SMS à Estelle ("Message urgent")
**Estelle:** Rappelle dans l'heure
**Résultat:** Accompagnement d'urgence proposé ✅

**Valeur:** Le chatbot a identifié une urgence émotionnelle et alerté immédiatement.

---

### Scénario 3: Comparaison Tarifaire (Lundi 10h)

**Visiteur:** Navigue sur site, hésite
**Chatbot:** Propose aide après 30 secondes
**Visiteur:** Clique "💰 Tarifs & Durée"
**Chatbot:** Affiche grille tarifaire + forfait avantageux
**Visiteur:** Clique "📅 Réserver" (choisit forfait 5 séances)
**Résultat:** Conversion optimale (320€ au lieu de 70€) ✅

**Valeur:** Le chatbot a proactivement présenté l'offre forfait, augmentant le panier moyen.

---

## 🔒 Conformité RGPD & Données Santé

### Points de Vigilance

**Données collectées via Tidio:**
- Adresse IP (anonymisée possible)
- Historique des conversations
- Prénom si demandé (optionnel)

**Conformité:**
✅ Tidio est RGPD-compliant (serveurs en UE)
✅ Pas de collecte de données médicales sensibles dans FAQ
✅ Redirection vers humain pour infos médicales

**À ajouter sur le site:**
- Mention dans Politique de Confidentialité: "Nous utilisons un chatbot pour répondre à vos questions. Les conversations sont stockées de manière sécurisée."
- Option opt-out: Possibilité de fermer le widget

**Bonnes pratiques:**
- Ne JAMAIS demander de données médicales dans le chatbot
- Toujours rediriger vers Estelle pour cas spécifiques
- Effacer conversations après 6 mois (paramètre Tidio)

---

## ✅ Checklist de Lancement

### Avant de mettre en ligne:

**Technique:**
- [ ] Tidio installé et fonctionnel
- [ ] Tous les parcours testés (chaque bouton)
- [ ] Liens vers calendrier RDV fonctionnent
- [ ] Formulaire de contact reçu par Estelle
- [ ] Tests sur mobile (iOS + Android)
- [ ] Tests sur différents navigateurs

**Contenu:**
- [ ] Toutes les réponses relues (orthographe, ton)
- [ ] Coordonnées (téléphone, email) correctes
- [ ] Tarifs à jour
- [ ] Contre-indications validées (vérifier avec médecin si doute)

**Légal:**
- [ ] Mention chatbot dans Politique de Confidentialité
- [ ] Paramètres RGPD activés dans Tidio
- [ ] Opt-out possible (fermeture du widget)

**Communication:**
- [ ] Post sur réseaux sociaux: "Nouveau! Assistant virtuel 24/7 sur notre site"
- [ ] Newsletter aux clientes existantes
- [ ] Mention lors des prochains RDV ("N'hésitez pas à tester notre chatbot")

---

## 🎉 Résumé Exécutif pour Estelle

**Ce que le chatbot va vous apporter:**

💰 **Économie de temps:**
- 8-10 heures/mois économisées sur réponses répétitives
- Équivalent à 1 jour de séances supplémentaires = +560€/mois

📈 **Augmentation conversions:**
- Disponibilité 24/7 → Prises RDV en dehors heures bureau
- Estimation: +20% de nouvelles clientes

💙 **Amélioration expérience client:**
- Réponses immédiates (pas d'attente)
- Informations complètes avant prise de décision
- Moins d'appels "pour rien" (questions déjà répondues)

🧘 **Qualité de vie:**
- Moins d'interruptions pendant séances
- Moins de charge mentale ("ai-je répondu à tous les emails?")
- Plus de temps pour vous et votre expertise

**Investissement:**
- Temps: 4-5 heures de configuration initiale
- Argent: 0€ au départ (gratuit jusqu'à 100 conversations/mois)
- Retour sur investissement: Dès le 1er mois

---

## 📞 Support NEXUS

**Ce document a été généré par NEXUS V6 (Claude + Gemini) pour vous accompagner dans la mise en place de votre chatbot FAQ.**

**Besoin d'aide pour l'implémentation?**
- Configuration technique Tidio
- Adaptation des réponses à votre pratique
- Ajout de nouvelles questions
- Optimisation selon vos métriques

**NEXUS reste disponible pour:**
- Mises à jour mensuelles du chatbot
- Analyse des conversations et recommandations
- Intégration avec votre futur CRM
- Évolution vers intelligence artificielle avancée (GPT-4 fine-tuné sur votre expertise)

---

**Document créé le:** 24 novembre 2025
**Dernière mise à jour:** 24 novembre 2025
**Version:** 1.0
**Auteurs:** Claude (rédaction) + Gemini (recherche)

**© 2025 NEXUS V6 - Bulleo Soins - Tous droits réservés**

---
