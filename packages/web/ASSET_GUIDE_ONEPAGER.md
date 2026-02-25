\# LifeTimeCircle – Asset-Leitfaden (Web) • Onepager



Ziel: Bilder/Assets schnell sauber ablegen, konsistent benennen, performant einbinden – ohne PII/Leaks.



---



\## 1) Wo kommen welche Bilder hin?



\### A) Große Bilder / Hintergründe / Hero-Images (runtime, per URL)

\*\*Pfad:\*\* `packages/web/public/assets/...`  

\*\*Warum:\*\* Wird 1:1 ausgeliefert → ideal für CSS `url("/assets/...")`



\*\*Empfohlene Struktur:\*\*

\- `packages/web/public/assets/landing/`  (Landingpage / Hero / Sections)

\- `packages/web/public/assets/backgrounds/` (generische BGs, Texturen)

\- `packages/web/public/assets/qr/` (public-qr visuals, nur datenarm)

\- `packages/web/public/assets/ui/` (noise/grain, kleine bitmap textures)



\### B) Icons / SVGs / kleine Illustrationen (importierbar, build-bundled)

\*\*Pfad:\*\* `packages/web/src/assets/...`  

\*\*Warum:\*\* Vite bundelt \& hasht → ideal für `import icon from "...";`



\*\*Empfohlene Struktur:\*\*

\- `packages/web/src/assets/brand/`

\- `packages/web/src/assets/icons/`

\- `packages/web/src/assets/illustrations/`



---



\## 2) Naming (damit nichts ausufert)



\*\*Schema:\*\* `<purpose>-<subject>\_<variant>\_v<nr>.<ext>`



Beispiele:

\- `hero-bg-generic-car\_desktop\_v1.webp`

\- `hero-bg-generic-car\_desktop\_v1@2x.webp`

\- `hero-bg-generic-car\_mobile\_v1.webp`

\- `noise-soft\_v1.png`

\- `ltc-mark\_v1.svg`



Regeln:

\- nur `a-z`, `0-9`, `-`, `\_`

\- Version hochzählen, nie “final\_final2”



---



\## 3) Formate \& Größen (Best Practice)



\### Hintergründe / Fotos / Render:

\- \*\*Bevorzugt:\*\* `.webp` (optional zusätzlich `.avif`)

\- \*\*Desktop Standard:\*\* 2560×1440 oder 1920×1080

\- \*\*Wide Option (Hero):\*\* 2560×1080 (21:9)

\- \*\*Mobile:\*\* 1080×1350 oder 1440×2560 (je nach Layout)

\- \*\*Retina:\*\* `@2x` nur wenn nötig (sonst zu groß)



\### Icons / Logos:

\- \*\*SVG\*\* bevorzugt (clean, ohne eingebettete Bitmaps)



---



\## 4) Performance-Check (Pflicht vor Commit)



\- Hero-BG idealerweise \*\*< 500 KB\*\* (WebP), je nach Motiv

\- Keine riesigen PNGs für Fotos

\- Immer prüfen: Ladezeit + Visuelle Qualität



---



\## 5) Einbindung (Copy/Paste Snippets)



\### CSS Background (public/assets → URL)

```css

.ltc-landing {

&nbsp; background:

&nbsp;   radial-gradient(...),

&nbsp;   url("/assets/landing/hero-bg-generic-car\_desktop\_v1.webp") center / cover no-repeat,

&nbsp;   linear-gradient(...);

}

