# ADR-005 – Markenidentität und Asset-Rechte

**Status: PARTIALLY DECIDED (20.11.2026).** Die folgenden Inhaberentscheidungen gelten. Offen bleiben weitere Einzelfreigaben und die Release-Abnahme.

Arbeitstitel Chess & Chains. Eigene SVG-Schachfiguren sind vorhanden, liegen **noch nicht** im Starterpaket. Brett und Wort-/Bildmarke werden erst ausgearbeitet. Originaldateien gehören nach `design/source/` und/oder `assets/chess_pieces/source_svg/`, Render-Exports in `marketing/exports/` (ignoriert).

Vor Release: Urheberschaft, eventuelle Font-Lizenz, Farbpalette, Iconrechte, Markenkollision (DPMA/EUIPO), Favicon/App-ID, Bildnachweise, kommerzielle/derivative Nutzungsrechte festlegen. GPL/MPL-Lizenzierung des Codes erfasst nicht automatisch jede Marke oder grafische Quelldatei.

## Integrierter Designkandidat (20.11.2026)

Der direkte Arbeitsauftrag delegierte die Designauswahl für die lokale App-Vorschau. **Connected System** ist der gewählte Kandidat. Die geometrisch neu konstruierten SVGs für Signet und Fenster-Icon sowie ihre PNG-Exporte werden vom lokalen Tk-Prototyp geladen. Die bereitgestellten Vorlagen einschließlich der Figurenübersicht sind als Arbeitsquellen inventarisiert. Der Owner-Review und die Freigabe für öffentliche Asset-Nutzung bleiben OPEN.

Der Owner hat am 20.11.2026 den Push und einen Pull Request für den KI-unterstützten Designkandidaten einschließlich SVG-Entwürfen und Vorschauen beauftragt. Die Originalvorlagen sind im Assetregister als Referenzen erfasst. Die Freigabe für die weitere Nutzung und Auslieferung der Markenassets bleibt Teil dieses ADRs.

[Markenkonstruktion und Varianten](../design/CONNECTED_SYSTEM.md) · [Owner-Review](../design/OWNER_DESIGN_REVIEW.md) · [Assetregister](../design/ASSET_REGISTER.csv)

## Entscheidungen des Inhabers (20.11.2026)

- **Connected System** ist die Markenrichtung. **Manufacturing Consent Regular** setzt die Wortmarke und prägnante große Überschriften. Normaler UI-Text bleibt gut lesbar. Das zugehörige Schriftrollensystem orientiert sich an Glide.
- Der **Inhaber gestaltet und liefert die Bretter**. Unterstützte Übergabeformen sind zwei Grundfelder, einzelne benannte Abweichungen, 64 benannte Felder und ein Gesamtbrett. Die Formate sind in der [SVG-Lieferanleitung](../../assets/boards/source/README.md) beschrieben.
- **Editierbare SVG- und Vektormaster haben Vorrang.** Produktionspfade und erforderliche Raster-Fallbacks werden zusätzlich aus den Mastern abgeleitet.
- **Tim von Trostorff** bestätigt, dass die Schachfiguren seine eigenen Entwürfe sind und er alle Rechte hält. Die Figuren dürfen innerhalb der App unter MPL-2.0 angeboten werden. Der [Originalmaster und seine Provenienz](../../assets/chess_pieces/source_svg/masters/PROVENANCE.md) sind dokumentiert. Aufbereitung, Rendering- und Paketprüfung bleiben für die Integration erforderlich.
- **Der Inhaber entscheidet und erteilt die Freigaben.** Die Herausgeberangabe orientiert sich am öffentlichen Glide-Installer, der Tim von Trostorff als Publisher nennt. Weitere Angaben für ein späteres Impressum benötigen den belegten Geltungsbereich. [Glide-Installerdefinition](https://github.com/n05a-design/glide-to-do/blob/bde7fa12ed048273f2916d21ad1e06b3a0426d0b/01_Repository/Glide/packaging/windows/glide_setup.iss)

## Figuren im lokalen Prototyp

Die 24 [bearbeitbaren App-Exporte](../../assets/chess_pieces/source_svg/README.md) stammen aus den Vorder- und Draufsichten des freigegebenen Masters. Der Inhaber hat am 21.11.2026 gleiche sichtbare Breite und Höhe je Figurentyp innerhalb einer Ansicht bestätigt und die Draufsicht visuell freigegeben. Aus der Referenz ergibt sich für die Vorderansicht ein gemeinsames Außenmaß von 39 × 54 Einheiten. Die Draufsicht verwendet 52 × 52 Einheiten. Beide Maße schließen die Kontur ein und beziehen sich auf eine 64 × 64 SVG-Fläche. Tk 9 liest die SVGs. Tk ohne SVG-Lesefunktion nutzt die vorab erzeugte PNG-Grafiktafel der gewählten Ansicht. Partie und Rätsel unterstützen beide Sätze. Sichtfreigabe der korrigierten Vorderansicht und Plattformabnahme bleiben offen.
