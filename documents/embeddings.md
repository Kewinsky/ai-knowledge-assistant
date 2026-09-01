# Embeddingi

## Reprezentacja tekstu
Embeddingi reprezentują tekst jako wektory liczb zmiennoprzecinkowych. Teksty
o podobnym znaczeniu powinny otrzymywać wektory położone blisko siebie, nawet
jeśli nie używają dokładnie tych samych słów.

## Zastosowania
Embeddingi wykorzystuje się między innymi w wyszukiwaniu semantycznym,
grupowaniu dokumentów, systemach rekomendacji i wykrywaniu podobnych treści.
W systemie RAG embedding pytania jest porównywany z embeddingami fragmentów
bazy wiedzy.

## Ograniczenia
Wektory utworzone przez różne modele nie powinny być bezpośrednio porównywane,
ponieważ mogą mieć inne wymiary i reprezentować tekst w innej przestrzeni.
Zmiana modelu embeddingowego wymaga ponownego utworzenia embeddingów całej
bazy wiedzy.
