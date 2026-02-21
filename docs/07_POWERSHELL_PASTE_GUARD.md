\# PowerShell Paste-Guard (Ctrl+Shift+V)



\## Problem

Beim Copy/Paste aus Chat/Docs landen oft Prompt-Zeilen wie `PS C:\\...>` im Clipboard.

PowerShell interpretiert diese Tokens als Commands/Fragmente und verursacht Folgefehler (z.B. ParserError / Get-Process).



\## Fix-Design (bindend)

\- Paste-Guard über `PSReadLine`-KeyHandler auf `Ctrl+Shift+V`.

\- Der Handler liest `Get-Clipboard -Raw` und verarbeitet zeilenweise.

\- Prompt-Prefix wird nur am Zeilenanfang entfernt per Regex: `^\\s\*PS\\s+.+?>\\s\*`.

\- Entfernt wird ausschließlich der Prefix; der restliche Command-Text bleibt unverändert.



\## Arbeitsregel (bindend)

\- Commands nur per `Ctrl+Shift+V` einfügen (Paste-Guard aktiv).

\- Normales `Ctrl+V` ist für Commands tabu.



\## Kill-Switch / Recovery

```powershell

Remove-Item Function:\\prompt -ErrorAction SilentlyContinue

. $PROFILE

