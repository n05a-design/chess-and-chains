# ADR-005 – Markenidentität und Asset-Rechte

**Status: PARTIALLY DECIDED (20.11.2026).** Die folgenden Inhaberentscheidungen gelten. Offen bleiben weitere Einzelfreigaben und die Release-Abnahme.

**Ausgangslage im historischen Starter F0.** Der Arbeitstitel lautete Chess & Chains. Die SVG-Schachfiguren lagen nur als Entwurf vor. Für die inzwischen integrierten Figuren und Markenassets gelten die Inhaberentscheidungen weiter unten. Originaldateien liegen in `design/source/` beziehungsweise `assets/chess_pieces/source_svg/`.

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

Die [historischen Designquellen](../../design/brand_exploration/README.md)
wurden am 21.11.2026 auf Auftrag des Inhabers für den Ablageabgleich
ins Repository übernommen. Das Assetregister dokumentiert die getrennte
Herkunft der lokalen Fontfassung und der App-Wortmarke. Die Abnahme von
Marken- und Release-Assets folgt den oben genannten Freigaben.

Die 24 [bearbeitbaren App-Exporte](../../assets/chess_pieces/source_svg/README.md) verwenden eine 64 × 64 SVG-Fläche. Der Inhaber hat am 21.11.2026 gleiche sichtbare Breite und Höhe je Figurentyp innerhalb einer Ansicht bestätigt und die Draufsicht visuell freigegeben. Die Draufsicht verwendet 52 × 52 Einheiten inklusive Kontur. Für die Vorderansicht gilt die nachgereichte Inhaberfassung einschließlich ihrer 1,14 Einheiten breiten Kontur. Ihre Pfade tragen eigene Innenschatten. Tk 9 liest die SVGs. Tk ohne SVG-Lesefunktion nutzt die vorab erzeugte PNG-Grafiktafel der gewählten Ansicht. Partie und Rätsel unterstützen beide Sätze. Sichtprüfung der Schattierung und Plattformabnahme bleiben offen.

## Marmor für die lokale 3D-Ansicht (21.11.2026)

Der Inhaber wählte für die 3D-Arbeitsfassung kühlen Marmor, einen
invertierten schwarzen Figurensatz und ein Brett mit 64 unterschiedlichen
Marmorfeldern. Die GitHub-Bereitstellung der Figurenaufbereitung, des
3D-Prototyps und der Studien wurde im Chat beauftragt. Für Produktpakete
und die endgültige Auswahl des App-Bretts gelten die offenen Release-
und Designentscheidungen. [Provenienz der Marmor-Dateien](../../design/source/marmor-3d/PROVENANCE.md)
