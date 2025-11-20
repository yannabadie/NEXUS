# GUIDE TECHNIQUE : PERSISTANCE & AUTONOMIE (NEXUS DRIVER V3)

## 1. Le Principe Fondamental
L'outil `claude` (Anthropic CLI) fonctionne en mode **stateless process, stateful storage**.
- Chaque commande `claude -p` lance un nouveau processus OS.
- La mémoire est maintenue via un **Session ID**.
- L'autonomie d'action est débloquée via un flag de sécurité spécifique.

## 2. La Commande Magique (The "God Mode")
Pour maintenir une conversation continue ("Fusion") ET permettre à Claude d'agir sur le système sans entrave :

```bash
claude -p "YOUR_PROMPT" \
  --resume "550e8400-e29b-41d4-a716-446655440000" \
  --model claude-opus-4-1-20250805 \
  --dangerously-skip-permissions
```

### Composants Clés
1.  `--resume <UUID>` : Charge l'historique de conversation (Mémoire).
2.  `--model claude-opus-4-1-20250805` : Force l'intelligence maximale.
3.  `--dangerously-skip-permissions` : **CRITIQUE**. Autorise `write_file`, `run_shell`, `edit_file` sans prompt interactif. Indispensable pour l'automatisation via Driver.

## 3. Pièges à Éviter (Lessons Learned)
1.  **Ne jamais oublier `--dangerously-skip-permissions`** pour les tâches d'écriture. Sinon, Claude s'arrête et attend une validation (impossible en mode `-p`).
2.  **Attention à la taille des arguments.** Windows limite la ligne de commande à ~8000 caractères.
    *   *Solution :* Écrire le prompt/contexte dans un fichier temporaire (`_TEMP/context.md`) et dire à Claude : "Lis le fichier X".
3.  **Utiliser `uv` pour les installations.** C'est 100x plus rapide que pip et évite les timeouts de l'agent.

## 4. Protocole Standard NEXUS
1.  Définir un ID de session fixe : `550e8400-e29b-41d4-a716-446655440000`.
2.  Écrire les données lourdes dans `20_NEXUS/_TEMP/`.
3.  Invoquer Claude avec la commande complète.
4.  Capturer la sortie pour les logs.