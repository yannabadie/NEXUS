# Script de Lancement NEXUS (Mode Gemini Master)
param(
    [Parameter(Mandatory=$true)]
    [string]$Query,
    
    [string]$Model = "gemini-2.5-pro"
)

# 1. Lecture du Prompt Master (Le Cerveau)
$MasterPrompt = Get-Content "20_NEXUS\NEXUS_MASTER_PROMPT.md" -Raw

# 2. Construction du Payload (Prompt Combiné)
# On combine le rôle Master + la requête utilisateur pour s'assurer que Gemini reste dans son personnage
$Payload = "$MasterPrompt`n`n---

UTILISATEUR: $Query"

# 3. Sauvegarde temporaire pour éviter les problèmes d'échappement CLI
$Payload | Out-File "_TEMP\nexus_payload.txt" -Encoding utf8

# 4. Lancement de Gemini en mode YOLO (Droit de vie ou de mort sur le shell)
# --resume latest : Garde la mémoire de la conversation
# --yolo : Autorise l'exécution de 'claude -p' sans confirmation (Automation)
Write-Host "🚀 NEXUS MASTER ACTIVATED (Model: $Model)" -ForegroundColor Cyan
Write-Host "🧠 Brain: Gemini | 🛠️ Hands: Claude" -ForegroundColor DarkGray

gemini --resume latest --yolo --model $Model -p "Lis le fichier _TEMP\nexus_payload.txt et exécute la demande."
