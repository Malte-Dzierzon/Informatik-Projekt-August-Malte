# Neuronales Netz zur Erkennung von Pyramiden

Ein einfaches neuronales Netz zur binären Klassifikation von 2D- und 3D-Objekten anhand ihrer Vertices.

## Projektziel
Das Modell entscheidet nur zwischen zwei Ausgaben:

- `1` = Pyramide
- `0` = keine Pyramide

## Eingabedaten
Als Input dienen die Koordinaten der Vertices eines Objekts.

- 2D-Objekte: `(x, y)`
- 3D-Objekte: `(x, y, z)`

Die Daten werden vor dem Training in einen festen Vektor umgewandelt und bei Bedarf normalisiert.

## Modellaufbau
- **Input Layer**: nimmt die Vertex-Daten auf
- **Hidden Layer**: erkennt geometrische Muster
- **Output Layer**: gibt `0` oder `1` aus

## Funktionsweise
Das Netzwerk lernt, typische Merkmale einer Pyramide zu erkennen, zum Beispiel eine Spitze und eine passende Basisstruktur.

## Trainingsdaten
Für das Training werden benötigt:

- positive Beispiele: verschiedene Pyramiden
- negative Beispiele: Würfel, Quader und andere Nicht-Pyramiden

## Projektstatus
Dieses Projekt dient als strukturierte Grundlage für ein Schulprojekt und kann später erweitert werden.

## Autoren
Malte und August