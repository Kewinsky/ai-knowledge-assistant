# Chunking dokumentów

## Cel
Chunking dzieli duży dokument na mniejsze fragmenty, które można niezależnie
indeksować i wyszukiwać. Do modelu trafia wtedy tylko część dokumentu związana
z pytaniem, a nie cała jego zawartość.

## Rozmiar fragmentu
Zbyt duże fragmenty mogą zawierać wiele niepowiązanych tematów i zużywać dużo
miejsca w kontekście modelu. Zbyt małe fragmenty mogą utracić informacje
potrzebne do zrozumienia zdania. Rozmiar należy dobrać do rodzaju dokumentów
i pytań użytkowników.

## Granice semantyczne
Dobry podział respektuje naturalne granice treści, takie jak akapity, sekcje
i nagłówki. Proste dzielenie po pustych liniach jest dobrym punktem startowym
dla dokumentów Markdown, ale nie gwarantuje fragmentów o równej długości.

## Overlap
Sąsiednie fragmenty mogą częściowo na siebie zachodzić. Taki overlap pomaga
zachować kontekst informacji znajdujących się na granicy dwóch fragmentów,
ale zwiększa liczbę embeddingów i koszt indeksowania.
