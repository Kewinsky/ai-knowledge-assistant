# RAG

## Podstawowa idea
Retrieval-Augmented Generation łączy wyszukiwanie informacji w bazie wiedzy
z generowaniem odpowiedzi przez model językowy. Model otrzymuje pytanie oraz
najbardziej pasujące fragmenty dokumentów jako kontekst.

## Przepływ danych
Dokumenty są wczytywane, dzielone na fragmenty i zamieniane na embeddingi.
Pytanie użytkownika również otrzymuje embedding, który jest porównywany z
wektorami fragmentów. Najlepsze wyniki trafiają do promptu modelu generującego
odpowiedź.

## Grounding
Odpowiedź powinna opierać się wyłącznie na przekazanym kontekście. Jeśli
dokumenty nie zawierają potrzebnej informacji, model powinien jasno powiedzieć,
że nie zna odpowiedzi, zamiast uzupełniać brakujące fakty własną wiedzą.

## Źródła
System powinien zachować ścieżkę i indeks każdego znalezionego fragmentu.
Dzięki temu może wyświetlić źródła odpowiedzi, a użytkownik może sprawdzić,
czy wygenerowane twierdzenia mają pokrycie w dokumentach.
