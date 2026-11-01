# Skills de terceros instaladas

| Origen | Qué se instaló | Dónde |
|---|---|---|
| nidhinjs/prompt-master | prompt-master | .claude/skills/ |
| DietrichGebert/ponytail | ponytail, ponytail-audit, -debt, -gain, -help, -review | .claude/skills/ |
| rtk-ai/rtk | binario v0.49.0 (SHA-256 fijado) + hook PreToolUse | .claude/hooks/install-rtk.sh, .claude/settings.json |
| affaan-m/ECC | 14 agentes + token-budget-advisor (sin hooks) | .claude/agents/, .claude/skills/ |
| addyosmani/agent-skills | 25 skills de ingeniería | .claude/skills/ |
| Leonxlnx/taste-skill | taste-skill | .claude/skills/ |
| nextlevelbuilder/ui-ux-pro-max-skill | ui-ux-pro-max, design, design-system, brand, banner-design, slides, ui-styling | .claude/skills/ |
| microsoft/playwright-cli | playwright-cli (requiere `npm i -g @playwright/cli@0.1.23`) | .claude/skills/ |
| VoltAgent/awesome-design-md | 84 DESIGN.md de referencia (no es una skill) | docs/awesome-design-md/ |

Copiadas de la rama por defecto de cada repo el 2026-11-01. Se eliminaron las carpetas `tests/` incluidas.

## Análisis de malware (mukul975/Anthropic-Cybersecurity-Skills, commit 54a7988)

performing-static-malware-analysis-with-pe-studio, performing-malware-triage-with-yara, analyzing-packed-malware-with-upx-unpacker, reverse-engineering-malware-with-ghidra, reverse-engineering-dotnet-malware-with-dnspy, extracting-iocs-from-malware-samples, analyzing-malware-persistence-with-autoruns.
Revisadas por patrones de riesgo y con Windows Defender: 0 detecciones.
