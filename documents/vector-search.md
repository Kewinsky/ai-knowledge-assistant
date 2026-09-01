# Wyszukiwanie wektorowe

## Wyszukiwanie semantyczne
Wyszukiwanie wektorowe porównuje embedding pytania z embeddingami fragmentów
dokumentów. Dzięki temu może znaleźć treści podobne znaczeniowo, nawet kiedy
pytanie i dokument używają innych słów.

## Cosine similarity
Cosine similarity mierzy kąt pomiędzy dwoma wektorami. Wartość bliska 1 oznacza
podobny kierunek, wartość bliska 0 brak wyraźnego podobieństwa, a wartość bliska
-1 kierunki przeciwne. Oba porównywane wektory muszą mieć ten sam wymiar.

## Ranking
Dla każdego fragmentu obliczany jest score podobieństwa. Wyniki są sortowane
malejąco, a kilka najlepiej ocenionych fragmentów trafia do dalszego etapu RAG.
Liczba zwracanych wyników jest często określana jako top-k.

## Ograniczenia
Wysoki score nie gwarantuje, że fragment rzeczywiście zawiera odpowiedź.
Jakość wyszukiwania zależy również od modelu embeddingowego, sposobu podziału
dokumentów i treści pytania. Dlatego retrieval należy oceniać na rzeczywistym
zestawie pytań.
