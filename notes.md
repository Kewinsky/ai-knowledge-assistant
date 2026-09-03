# AI Engineering Knowledge Assistant — notatki

## Ticket 1: wczytywanie dokumentów Markdown

### Cel

Pierwszy ticket wprowadził loader dokumentów. Jego zadaniem jest znalezienie
plików Markdown w podanym katalogu oraz wczytanie ich treści do pamięci.

Aktualna funkcja znajduje się w `knowledge_assistant/documents.py`:

```python
def load_markdown_files(directory: str | Path) -> list[Document]:
```

### Jak działa loader

1. Argument zostaje zamieniony na obiekt `Path`.
2. Program sprawdza, czy podana ścieżka jest istniejącym katalogiem.
3. `rglob("*.md")` wyszukuje pliki Markdown również w podkatalogach.
4. `sorted()` zapewnia zawsze tę samą kolejność plików.
5. Każdy plik jest odczytywany jako tekst w kodowaniu UTF-8.
6. Ścieżka i treść są dodawane do listy dokumentów.

```python
for file_path in sorted(directory_path.rglob("*.md")):
    if file_path.is_file():
        content = file_path.read_text(encoding="utf-8")
```

`rglob()` może zwrócić również pasującą ścieżkę, która nie jest zwykłym
plikiem. Dlatego kod dodatkowo sprawdza `file_path.is_file()`.

### Dlaczego używamy `Path`

`Path` reprezentuje ścieżkę jako obiekt. Dzięki temu można korzystać z metod
takich jak:

- `is_dir()` — sprawdzenie, czy ścieżka jest katalogiem,
- `is_file()` — sprawdzenie, czy ścieżka jest plikiem,
- `read_text()` — odczyt tekstu,
- `rglob()` — rekurencyjne wyszukiwanie plików.

Jest to czytelniejsze i łatwiejsze do przenoszenia między systemami niż ręczne
łączenie ścieżek za pomocą stringów.

### Ważne decyzje

- Jawne `encoding="utf-8"` zapobiega zależności od domyślnego kodowania systemu.
- `sorted()` daje deterministyczny wynik, co ułatwia testowanie i debugowanie.
- Niepoprawny katalog powoduje `NotADirectoryError`, zamiast cichego zwrócenia
  pustej listy.
- Loader odpowiada tylko za odczyt dokumentów. Nie dzieli treści i nie wykonuje
  wyszukiwania.

### Pytania rekrutacyjne

- Czym różni się `glob()` od `rglob()`?
- Dlaczego warto jawnie podawać kodowanie pliku?
- Dlaczego deterministyczna kolejność danych jest ważna?
- Kiedy lepiej zgłosić wyjątek, a kiedy zwrócić pustą listę?

### Keywords

- **Loader** — kod odpowiedzialny za wczytanie danych z zewnętrznego źródła.
- **`Path`** — obiekt ze standardowej biblioteki reprezentujący ścieżkę.
- **Markdown** — prosty format tekstowy używający rozszerzenia `.md`.
- **`glob()`** — wyszukuje ścieżki pasujące do podanego wzorca.
- **`rglob()`** — wyszukuje pasujące ścieżki również w podkatalogach.
- **Rekurencyjne wyszukiwanie** — przeglądanie katalogu i jego podkatalogów.
- **UTF-8** — popularne kodowanie znaków obsługujące między innymi polskie litery.
- **Deterministyczność** — te same dane wejściowe dają wynik w tej samej kolejności.
- **Wyjątek** — informacja o błędzie przerywająca normalny przepływ funkcji.

---

## Ticket 2: model dokumentu za pomocą `dataclass`

### Cel

Loader początkowo zwracał listę krotek:

```python
list[tuple[Path, str]]
```

Odczyt danych wyglądał wtedy tak:

```python
document[0]
document[1]
```

Nie wiadomo od razu, co oznaczają indeksy `0` i `1`. Dlatego powstał jawny
model danych:

```python
@dataclass
class Document:
    path: Path
    content: str
```

Teraz kod może używać czytelnych nazw:

```python
document.path
document.content
```

### Co daje `@dataclass`

Dekorator `@dataclass` automatycznie tworzy podstawowe elementy klasy, przede
wszystkim konstruktor `__init__()`.

Dzięki temu można utworzyć dokument tak:

```python
document = Document(
    path=Path("documents/python.md"),
    content="Python jest językiem programowania.",
)
```

Bez `@dataclass` należałoby samodzielnie napisać konstruktor i przypisania pól.

### Dlaczego model jest lepszy od krotki

- Pola mają nazwy opisujące ich znaczenie.
- Edytor może podpowiadać dostępne pola.
- Type checker może sprawdzić oczekiwane typy.
- Łatwiej dodać kolejne pole bez zmieniania znaczenia indeksów.
- Kod jest prostszy do czytania podczas review i debugowania.

### Type hints nie wykonują automatycznej walidacji

Zapis:

```python
path: Path
content: str
```

opisuje oczekiwane typy, ale zwykłe uruchomienie Pythona ich nie wymusza.
Adnotacje są wykorzystywane przede wszystkim przez programistę, edytor oraz
narzędzia do statycznej analizy.

### Ważne decyzje

- `Document` jest modelem danych, a nie serwisem.
- Nie zawiera logiki wczytywania plików.
- Nie dodano walidacji ani metod, ponieważ nie były jeszcze potrzebne.
- Funkcja loadera jawnie zwraca `list[Document]`.

### Pytania rekrutacyjne

- Czym `dataclass` różni się od zwykłej klasy?
- Dlaczego nazwane pola są czytelniejsze od indeksów krotki?
- Czy type hints są sprawdzane podczas działania programu?
- Kiedy prosta krotka nadal może być dobrym wyborem?

### Keywords

- **Model danych** — struktura opisująca dane używane przez aplikację.
- **`dataclass`** — dekorator generujący podstawowy kod klasy przechowującej dane.
- **Dekorator** — funkcja zmieniająca lub rozszerzająca zachowanie innej definicji.
- **Pole** — nazwana wartość przechowywana w obiekcie.
- **Instancja** — konkretny obiekt utworzony na podstawie klasy.
- **Krotka (`tuple`)** — uporządkowana i niemutowalna kolekcja wartości.
- **Type hint** — adnotacja opisująca oczekiwany typ wartości.
- **Statyczna analiza** — sprawdzanie kodu bez jego normalnego uruchamiania.
- **Czytelność kodu** — łatwość zrozumienia znaczenia i działania kodu.

---

## Ticket 3: podział dokumentów na fragmenty

### Cel

Cały dokument może być zbyt duży i zawierać kilka różnych tematów. Ticket 3
wprowadził dzielenie dokumentów na mniejsze fragmenty, czyli chunki.

Model fragmentu wygląda tak:

```python
@dataclass
class DocumentChunk:
    document_path: Path
    index: int
    content: str
```

Fragment zachowuje ścieżkę dokumentu źródłowego. Dzięki temu później można
pokazać użytkownikowi źródło znalezionej informacji.

### `split_document()`

Funkcja dzieli pojedynczy dokument:

```python
def split_document(document: Document) -> list[DocumentChunk]:
```

Najważniejsza operacja:

```python
document.content.split("\n\n")
```

`split("\n\n")` przecina tekst w miejscach, gdzie znajdują się dwie nowe linie,
czyli typowa pusta linia oddzielająca akapity Markdown.

Każdy otrzymany fragment jest następnie czyszczony:

```python
content = part.strip()
```

`strip()` usuwa białe znaki wyłącznie z początku i końca tekstu. Nie zmienia
środka fragmentu.

Puste fragmenty są pomijane:

```python
if content:
```

Indeks jest nadawany za pomocą aktualnej długości listy:

```python
index=len(chunks)
```

Dzięki temu indeksy nie mają przerw, nawet gdy po drodze pominięto pusty tekst.

### `split_documents()`

Ta funkcja wykonuje podział dla wielu dokumentów:

```python
def split_documents(documents: list[Document]) -> list[DocumentChunk]:
```

Dla każdego dokumentu wywołuje `split_document()`, a wyniki dodaje przez:

```python
chunks.extend(split_document(document))
```

`extend()` dodaje każdy element przekazanej listy osobno. Dzięki temu wynik jest
jedną płaską listą.

Gdyby użyć `append()`, powstałaby lista zagnieżdżona:

```python
list[list[DocumentChunk]]
```

Można powiedzieć, że `extend()` jest podobne do użycia spread operatora na
elementach tablicy w JavaScript.

### Brak modyfikacji dokumentu wejściowego

Funkcja tylko odczytuje `document.content` i tworzy nowe obiekty
`DocumentChunk`. Oryginalny `Document` pozostaje bez zmian. Ułatwia to
przewidywanie działania kodu i ogranicza efekty uboczne.

### Ograniczenia prostego podziału

- Fragmenty mogą mieć bardzo różne długości.
- Nagłówek może zostać oddzielony od opisującego go akapitu.
- Informacja na granicy dwóch fragmentów może utracić część kontekstu.
- Nie ma maksymalnego rozmiaru ani nakładania się fragmentów.

Jest to jednak dobry i prosty punkt startowy.

### Pytania rekrutacyjne

- Czym różni się `split()` od `strip()`?
- Czym różni się `append()` od `extend()`?
- Dlaczego indeks fragmentu powinien zaczynać się od zera?
- Dlaczego fragment powinien przechowywać ścieżkę dokumentu źródłowego?
- Jakie problemy może powodować zbyt duży lub zbyt mały chunk?

### Keywords

- **Chunk** — mniejszy fragment większego dokumentu.
- **Chunking** — proces dzielenia dokumentów na mniejsze części.
- **`split()`** — dzieli string na części według podanego separatora.
- **`strip()`** — usuwa białe znaki z początku i końca stringa.
- **Białe znaki** — między innymi spacja, tabulator i znak nowej linii.
- **`append()`** — dodaje jeden obiekt na koniec listy.
- **`extend()`** — dodaje do listy wszystkie elementy innej kolekcji.
- **Płaska lista** — lista zawierająca elementy bez dodatkowego poziomu list.
- **Indeks** — pozycja elementu; w Pythonie zazwyczaj zaczyna się od zera.
- **Efekt uboczny** — zmiana stanu poza wartością zwracaną przez funkcję.

---

## Ticket 4: proste wyszukiwanie tekstowe

### Cel

Ticket 4 wprowadził pierwszą wersję wyszukiwarki. Nie rozumie ona znaczenia
tekstu. Liczy jedynie unikalne słowa wspólne dla pytania i fragmentu.

Przepływ wygląda tak:

```text
pytanie -> tokenizacja -> ocena fragmentów -> sortowanie -> top wyników
```

### Tokenizacja

```python
def tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))
```

Funkcja wykonuje trzy rzeczy:

1. `lower()` zamienia tekst na małe litery.
2. `re.findall(r"\w+", ...)` znajduje słowa i pomija interpunkcję.
3. `set(...)` usuwa duplikaty.

Dzięki temu:

```python
tokenize("Python, python i RAG!")
```

daje zbiór podobny do:

```python
{"python", "i", "rag"}
```

W Pythonie `\w` domyślnie obsługuje znaki Unicode, więc rozpoznaje również
polskie litery.

### Obliczanie score

```python
chunk_tokens = tokenize(chunk.content)
return len(query_tokens & chunk_tokens)
```

Operator `&` wyznacza część wspólną dwóch zbiorów. Wynikiem score jest liczba
unikalnych słów obecnych zarówno w pytaniu, jak i fragmencie.

Powtórzenie słowa nie zwiększa wyniku, ponieważ `set` przechowuje każdą wartość
tylko raz.

### Wyszukiwanie wielu fragmentów

`search_chunks()`:

1. Odrzuca niepoprawny `limit`.
2. Tokenizuje pytanie tylko raz.
3. Oblicza score każdego fragmentu.
4. Pomija wyniki ze score równym zero.
5. Sortuje pasujące wyniki.
6. Zwraca najwyżej `limit` elementów.

### Sortowanie deterministyczne

Klucz sortowania ma postać:

```python
def sort_key(result: SearchResult) -> tuple[int, str, int]:
    return (
        -result.score,
        str(result.chunk.document_path),
        result.chunk.index,
    )
```

Python porównuje elementy krotki od lewej do prawej:

1. Najpierw score malejąco. Minus odwraca kolejność wartości liczbowej.
2. Przy remisie ścieżka jest porównywana alfabetycznie.
3. Przy tej samej ścieżce decyduje indeks fragmentu.

`str(path)` tworzy tekstową reprezentację ścieżki, którą można jednoznacznie
porównać podczas sortowania.

Funkcja jest przekazywana jako `key`, ponieważ `sort()` potrzebuje informacji,
jaką wartość ma porównywać dla każdego elementu. Przekazujemy samą funkcję, a
`sort()` wywołuje ją później dla wyników.

### Ograniczenia wyszukiwania tekstowego

- Nie rozumie synonimów.
- `analiza` i `analizy` są różnymi tokenami.
- Wszystkie słowa mają taką samą wagę.
- Częste słowa, np. „i”, również wpływają na score.
- Nie rozpoznaje znaczenia całego zdania.

Ta wersja jest jednak ważnym baseline'em. Można ją później porównać z
wyszukiwaniem semantycznym i sprawdzić, czy bardziej złożona metoda faktycznie
daje lepsze wyniki.

### Pytania rekrutacyjne

- Dlaczego tokenizujemy pytanie tylko raz?
- Dlaczego używamy `set`, a nie `list`?
- Jak działa przecięcie zbiorów?
- Po co stosować deterministyczne rozstrzyganie remisów?
- Czym wyszukiwanie słów różni się od wyszukiwania semantycznego?
- Dlaczego warto zachować prosty baseline?

### Keywords

- **Tokenizacja** — podział tekstu na mniejsze jednostki, tutaj słowa.
- **Token** — pojedyncza jednostka otrzymana podczas tokenizacji.
- **Regex** — wyrażenie opisujące wzorzec wyszukiwanego tekstu.
- **`re.findall()`** — zwraca wszystkie fragmenty pasujące do wyrażenia regularnego.
- **`set`** — nieuporządkowany zbiór unikalnych wartości.
- **Przecięcie zbiorów** — wartości występujące jednocześnie w obu zbiorach.
- **Score** — liczbowy wynik określający dopasowanie fragmentu.
- **Ranking** — uporządkowanie wyników od najlepszego do najsłabszego.
- **Tie-breaker** — dodatkowa zasada rozstrzygająca wyniki z takim samym score.
- **Baseline** — proste rozwiązanie służące jako punkt odniesienia.
- **Top-k** — wybór `k` najwyżej ocenionych wyników.

---

## Ticket 5: podział kodu na moduły

### Cel

Na początku cały kod znajdował się w `main.py`. Z czasem plik zaczął odpowiadać
jednocześnie za modele danych, dokumenty, wyszukiwanie i interfejs terminalowy.
Ticket 5 rozdzielił te odpowiedzialności.

Pierwsza struktura pakietu wyglądała tak:

```text
knowledge_assistant/
├── __init__.py
├── models.py
├── documents.py
└── search.py
main.py
```

### Odpowiedzialności modułów

- `models.py` przechowuje modele danych.
- `documents.py` odpowiada za wczytywanie i dzielenie dokumentów.
- `search.py` zawiera logikę wyszukiwania tekstowego.
- `main.py` jest punktem wejścia i łączy kolejne elementy przepływu.

Taki podział stosuje zasadę separation of concerns: jeden moduł powinien mieć
jedną wyraźną odpowiedzialność.

### Moduł i pakiet

Pojedynczy plik `.py` jest modułem Pythona. Katalog zawierający moduły jest
pakietem. Plik `knowledge_assistant/__init__.py` jawnie oznacza katalog jako
pakiet i może kontrolować jego publiczny interfejs.

W tym projekcie `__init__.py` jest pusty, ponieważ nie potrzebujemy jeszcze
udostępniać skróconych importów ani wykonywać inicjalizacji pakietu.

### Jawne importy

Kod używa importów takich jak:

```python
from knowledge_assistant.models import Document, DocumentChunk
```

Jawny import pokazuje, skąd pochodzi dana nazwa. Należy unikać:

```python
from module import *
```

Import z gwiazdką utrudnia ustalenie pochodzenia nazw i może powodować ich
przypadkowe nadpisanie.

### Funkcja `main()`

Logika uruchomieniowa została zamknięta w funkcji:

```python
def main() -> None:
```

`-> None` oznacza, że funkcja nie zwraca wartości użytkowej. W późniejszych
ticketach `main()` zaczęło zwracać `int`, aby przekazywać kod zakończenia procesu.

Umieszczenie kodu w funkcji:

- ogranicza zmienne globalne,
- ułatwia testowanie,
- wyraźnie pokazuje punkt rozpoczęcia programu,
- zapobiega wykonaniu logiki podczas samego importu modułu.

### `if __name__ == "__main__"`

```python
if __name__ == "__main__":
    main()
```

Python ustawia specjalną zmienną `__name__`:

- na `"__main__"`, gdy plik został uruchomiony bezpośrednio,
- na nazwę modułu, gdy plik został zaimportowany.

Dzięki temu aplikacja uruchamia się dla:

```bash
python main.py
```

ale nie uruchamia automatycznie podczas:

```python
import main
```

Jest to standardowy wzorzec w aplikacjach i skryptach Pythona.

### Importowanie przez terminal

Polecenie:

```bash
python -c "import knowledge_assistant.documents; print('OK')"
```

nie jest specjalnym rodzajem importu. Opcja `-c` prosi Pythona o wykonanie
krótkiego kodu przekazanego jako tekst. Takie polecenie szybko sprawdza, czy:

- pakiet można znaleźć,
- importy są poprawne,
- nie ma błędów składni,
- moduły nie wypisują niczego podczas importowania.

### Zależności pomiędzy modułami

Prosty kierunek zależności wygląda następująco:

```text
models
  ↑
documents   search
  ↑           ↑
       main
```

Modele nie powinny importować logiki wyszukiwania ani interfejsu CLI. Moduły
wyższego poziomu korzystają z prostszych modułów niższego poziomu. Pomaga to
unikać importów cyklicznych.

### Ważne zasady

- Import modułu nie powinien uruchamiać aplikacji ani wykonywać requestów.
- `main.py` powinien zajmować się głównie orkiestracją i prezentacją wyniku.
- Logika domenowa powinna znajdować się w pakiecie.
- Podział na moduły powinien wynikać z odpowiedzialności, a nie z chęci
  utworzenia jak największej liczby plików.
- Mały projekt również może mieć dobrą strukturę, ale nie warto tworzyć
  abstrakcji, które nie rozwiązują realnego problemu.

### Pytania rekrutacyjne

- Czym różni się moduł od pakietu?
- Do czego służy `__init__.py`?
- Jak działa `if __name__ == "__main__"`?
- Dlaczego import nie powinien powodować efektów ubocznych?
- Co oznacza separation of concerns?
- Czym jest import cykliczny i dlaczego może być problemem?
- Co powinno znajdować się w `main.py`?

### Keywords

- **Moduł** — pojedynczy plik Pythona zawierający kod.
- **Pakiet** — katalog grupujący powiązane moduły Pythona.
- **`__init__.py`** — plik inicjalizujący pakiet i opcjonalnie jego publiczne API.
- **Entry point** — miejsce, od którego rozpoczyna się wykonanie aplikacji.
- **`__name__`** — specjalna zmienna zawierająca nazwę aktualnego modułu.
- **`__main__`** — wartość `__name__` dla pliku uruchomionego bezpośrednio.
- **Import** — udostępnienie kodu z innego modułu.
- **Jawny import** — import konkretnie wskazanych nazw.
- **Efekt uboczny importu** — działanie wykonane już podczas ładowania modułu.
- **Separation of concerns** — rozdzielenie różnych odpowiedzialności kodu.
- **Cohesion (spójność)** — stopień, w jakim elementy modułu dotyczą jednego celu.
- **Coupling (sprzężenie)** — poziom zależności pomiędzy modułami.
- **Import cykliczny** — sytuacja, gdy moduły bezpośrednio lub pośrednio
  importują siebie nawzajem.
- **Orkiestracja** — łączenie kilku kroków programu w jeden przepływ.

---

## Ticket 6: konfiguracja projektu za pomocą `uv`

### Cel

Ticket 6 wprowadził kontrolowane środowisko Pythona i powtarzalne zarządzanie
zależnościami. Dzięki temu projekt nie korzysta przypadkowo z bibliotek
zainstalowanych globalnie na komputerze.

Najważniejsze elementy to:

```text
pyproject.toml
uv.lock
.venv/
```

### `pyproject.toml`

`pyproject.toml` jest głównym plikiem opisującym projekt Pythona. Zawiera między
innymi:

- nazwę i wersję projektu,
- opis,
- obsługiwaną wersję Pythona,
- bezpośrednie zależności aplikacji,
- zależności używane tylko podczas developmentu.

Przykład:

```toml
[project]
name = "ai-engineering-knowledge-assistant"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = []
```

Zapis `>=3.14` jest ograniczeniem wersji. Oznacza, że projekt wymaga Pythona
3.14 lub nowszego. Nie oznacza, że każda maszyna automatycznie użyje dokładnie
tej samej poprawki, np. `3.14.1`.

### Środowisko wirtualne

`.venv/` zawiera interpreter i biblioteki przeznaczone dla tego projektu.
Oddziela je od:

- systemowego Pythona,
- innych projektów,
- pakietów zainstalowanych globalnie.

Dwa projekty mogą dzięki temu używać różnych wersji tej samej biblioteki bez
konfliktu.

`.venv/` nie trafia do repozytorium. Każdy programista może odtworzyć je na
podstawie plików projektu.

### `uv sync`

Polecenie:

```bash
uv sync
```

uzgadnia trzy elementy:

```text
pyproject.toml -> uv.lock -> .venv
```

W uproszczeniu:

1. `pyproject.toml` mówi, jakich zależności potrzebuje projekt.
2. `uv.lock` zapisuje dokładnie rozwiązany zestaw wersji.
3. `.venv` otrzymuje pakiety wynikające z lockfile'a.

### `uv.lock`

`uv.lock` przechowuje dokładne informacje o rozwiązanych zależnościach, także
zależnościach pośrednich.

Powinien być commitowany do repozytorium, ponieważ pomaga odtworzyć spójne
środowisko na różnych komputerach i w CI.

Pliku nie należy edytować ręcznie. Zarządza nim `uv`.

### `uv run`

Polecenie:

```bash
uv run python main.py "pytanie"
```

uruchamia program w środowisku projektu. `uv` wcześniej sprawdza, czy środowisko
i lockfile są aktualne.

Nie trzeba ręcznie wykonywać:

```bash
source .venv/bin/activate
```

Ręczna aktywacja nadal jest możliwa, ale `uv run` jest wygodne w skryptach,
CI oraz dokumentacji, ponieważ jawnie wskazuje środowisko wykonania.

### Dodawanie zależności

```bash
uv add openai
```

To polecenie:

- dodaje bibliotekę do `pyproject.toml`,
- aktualizuje `uv.lock`,
- aktualizuje środowisko `.venv`.

Zależność używaną tylko podczas tworzenia projektu można dodać przez:

```bash
uv add --dev pytest
```

### Ważne decyzje

- `.venv/` jest ignorowane przez Git, ponieważ można je odtworzyć.
- `uv.lock` jest commitowany, ponieważ zapewnia powtarzalność instalacji.
- Zależności dodajemy przez `uv add`, zamiast ręcznie instalować je globalnie.
- `uv` zarządza środowiskiem i zależnościami, ale nie zmienia zasad działania
  samego Pythona.

### Pytania rekrutacyjne

- Po co używa się środowiska wirtualnego?
- Czym różni się `pyproject.toml` od `uv.lock`?
- Dlaczego `.venv` nie powinno trafiać do repozytorium?
- Dlaczego lockfile powinien być commitowany?
- Czym różni się zależność bezpośrednia od pośredniej?
- Co robi `uv sync`, a co robi `uv run`?

### Keywords

- **`uv`** — narzędzie do zarządzania Pythonem, środowiskiem i zależnościami.
- **Środowisko wirtualne** — izolowane środowisko Pythona dla jednego projektu.
- **`.venv`** — typowa nazwa katalogu ze środowiskiem wirtualnym projektu.
- **`pyproject.toml`** — standardowy plik metadanych i konfiguracji projektu.
- **Zależność** — zewnętrzna biblioteka potrzebna aplikacji.
- **Zależność pośrednia** — biblioteka wymagana przez inną zależność.
- **Lockfile** — plik zapisujący dokładnie rozwiązane wersje zależności.
- **`uv.lock`** — lockfile zarządzany przez `uv`.
- **Reproducibility** — możliwość odtworzenia takiego samego środowiska.
- **Dependency resolution** — wybieranie zgodnych wersji wszystkich zależności.
- **`uv sync`** — synchronizacja lockfile'a i środowiska projektu.
- **`uv run`** — uruchomienie polecenia w środowisku projektu.

---

## Ticket 7: generowanie embeddingów

### Cel

Ticket 7 dodał zamianę treści fragmentów dokumentów na embeddingi. Embedding
jest listą liczb reprezentującą znaczenie tekstu w przestrzeni wektorowej.

Model danych wygląda tak:

```python
@dataclass
class EmbeddedChunk:
    chunk: DocumentChunk
    embedding: list[float]
```

Obiekt zachowuje zarówno oryginalny fragment, jak i odpowiadający mu wektor.

### Czym jest embedding

Embedding nie jest listą słów ani zakodowanym zdaniem, które można łatwo
odczytać. Jest to wektor liczb zmiennoprzecinkowych, np. w bardzo uproszczonej
postaci:

```python
[0.12, -0.08, 0.31, ...]
```

Model embeddingowy został wcześniej wytrenowany na dużej liczbie przykładów.
Nauczył się umieszczać teksty o podobnym znaczeniu w podobnych obszarach
przestrzeni wektorowej.

Wektor nie jest losowany przy każdym porównaniu. Powstaje przez wykonanie modelu
embeddingowego dla konkretnego tekstu.

### Model embeddingowy a model generujący

Model embeddingowy:

```text
tekst -> wektor liczb
```

Model generujący:

```text
instrukcje + tekst -> odpowiedź tekstowa
```

To dwa różne zadania. Model embeddingowy nie odpowiada użytkownikowi, a model
generujący nie jest w tym projekcie używany do obliczania podobieństwa.

### `create_embeddings()`

```python
def create_embeddings(
    client: OpenAI,
    texts: list[str],
) -> list[list[float]]:
```

Funkcja:

1. Dla pustej listy zwraca `[]` bez requestu.
2. Odrzuca tekst pusty po `strip()`.
3. Przekazuje wszystkie teksty w jednym requeście.
4. Sprawdza liczbę wektorów w odpowiedzi.
5. Porządkuje odpowiedź według pola `index`.
6. Zwraca same embeddingi.

```python
response = client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=texts,
    dimensions=EMBEDDING_DIMENSIONS,
)
```

Wysłanie listy tekstów w jednym wywołaniu nazywamy batchingiem. Ogranicza ono
liczbę requestów i zwykle jest wydajniejsze niż osobne wywołanie dla każdego
fragmentu.

### Dlaczego sortujemy odpowiedź po `index`

Każdy element odpowiedzi API zawiera indeks odpowiadającego mu tekstu
wejściowego. Kod nie powinien opierać dopasowania wyłącznie na przypadkowej
kolejności elementów odpowiedzi.

```python
ordered_embeddings = sorted(response.data, key=embedding_index)
```

`sorted()` tworzy nową listę. W przeciwieństwie do tego `list.sort()` zmienia
istniejącą listę i zwraca `None`.

### `embed_chunks()`

Najpierw pobierana jest treść każdego fragmentu:

```python
texts = [chunk.content for chunk in chunks]
```

Następnie wszystkie teksty są wysyłane do `create_embeddings()`. Pętla z
`zip()` łączy każdy wcześniejszy chunk z odpowiadającym mu wektorem:

```python
for chunk, embedding in zip(chunks, embeddings, strict=True):
```

Bez tej pętli mielibyśmy dwie osobne listy i nie byłoby wygodnego obiektu
mówiącego: „ten embedding należy do tego fragmentu”.

`strict=True` zgłasza błąd, jeżeli listy mają różne długości. Zapobiega cichemu
zgubieniu nadmiarowych elementów.

### Dlaczego klient jest argumentem

```python
create_embeddings(client, texts)
```

Funkcja nie tworzy klienta OpenAI wewnątrz. Jest to prosta forma dependency
injection:

- konfiguracja klienta pozostaje poza logiką,
- jeden klient może być używany w wielu funkcjach,
- w testach można przekazać mock,
- funkcja jest łatwiejsza do kontrolowania.

### Klucz API

Klucz jest sekretem i powinien znajdować się w zmiennej środowiskowej:

```bash
export OPENAI_API_KEY="..."
```

Nie należy umieszczać go w kodzie, commitach, logach ani plikach przesyłanych do
repozytorium. Klient `OpenAI()` może odczytać go ze środowiska.

### Ważne ograniczenia

- Requesty do API mogą kosztować pieniądze.
- Wektor sam w sobie nie wyjaśnia, dlaczego teksty są podobne.
- Wektory z różnych modeli lub o różnych wymiarach nie powinny być porównywane.
- Zmiana modelu wymaga ponownego wygenerowania embeddingów dokumentów.
- Długi tekst może przekroczyć limit wejścia modelu embeddingowego.

### Pytania rekrutacyjne

- Czym jest embedding i do czego można go wykorzystać?
- Czym model embeddingowy różni się od LLM generującego tekst?
- Dlaczego teksty wysyłamy w jednym requeście?
- Po co odpowiedź API ma pole `index`?
- Czym różni się `sorted()` od `list.sort()`?
- Co daje `zip(..., strict=True)`?
- Dlaczego klient API przekazujemy jako argument?
- Gdzie należy przechowywać klucz API?

### Keywords

- **Embedding** — numeryczna reprezentacja znaczenia danych, np. tekstu.
- **Wektor** — uporządkowana lista liczb.
- **Wymiar wektora** — liczba wartości znajdujących się w wektorze.
- **Przestrzeń wektorowa** — matematyczna przestrzeń, w której znajdują się wektory.
- **Model embeddingowy** — model zamieniający dane na embeddingi.
- **Podobieństwo semantyczne** — podobieństwo znaczenia, a nie tylko wspólnych słów.
- **Batching** — przetwarzanie wielu elementów w jednym wywołaniu.
- **Request API** — żądanie wysyłane przez aplikację do zewnętrznej usługi.
- **Response API** — odpowiedź zwracana przez usługę.
- **SDK** — biblioteka ułatwiająca korzystanie z danego API.
- **Dependency injection** — przekazanie zależności z zewnątrz zamiast tworzenia jej wewnątrz.
- **`zip()`** — łączy elementy kilku kolekcji według ich pozycji.
- **List comprehension** — skrócony zapis tworzenia listy na podstawie iteracji.
- **API key** — sekret używany do uwierzytelniania requestów.

---

## Ticket 8: wyszukiwanie semantyczne i cosine similarity

### Cel

Ticket 8 umożliwił porównanie embeddingu pytania z embeddingami fragmentów.
Dzięki temu wyszukiwarka może znaleźć podobne znaczenie, nawet gdy pytanie i
dokument nie zawierają dokładnie tych samych słów.

### Model wyniku

```python
@dataclass
class SemanticSearchResult:
    chunk: DocumentChunk
    score: float
```

Wynik przechowuje fragment oraz liczbową wartość podobieństwa.

### Cosine similarity

Cosine similarity mierzy kąt pomiędzy dwoma wektorami:

```text
similarity = dot_product / (left_magnitude * right_magnitude)
```

Typowa interpretacja:

- wartość bliska `1` — podobny kierunek,
- wartość bliska `0` — brak wyraźnego podobieństwa kierunku,
- wartość bliska `-1` — przeciwne kierunki.

W przypadku embeddingów dokładna interpretacja score zależy od modelu i danych.
Score nie jest procentem ani gwarancją, że fragment zawiera odpowiedź.

### Iloczyn skalarny

```python
dot_product = sum(
    left_value * right_value
    for left_value, right_value in zip(left, right, strict=True)
)
```

Kod bierze pary liczb z tych samych pozycji, mnoży je i sumuje wyniki.

Dla wektorów:

```text
[a, b] oraz [c, d]
```

iloczyn skalarny wynosi:

```text
a*c + b*d
```

### Długość wektora

```python
left_magnitude = math.sqrt(sum(value**2 for value in left))
```

`value**2` oznacza podniesienie wartości do drugiej potęgi. Wyrażenie:

```python
value**2 for value in left
```

jest generator expression. Działa podobnie do transformacji `.map()` w
JavaScript, ale przekazuje wartości leniwie, bez tworzenia dodatkowej listy.

### Walidacja wektorów

Funkcja odrzuca:

- wektory o różnych długościach,
- puste wektory,
- wektory o długości, czyli normie, równej zero.

Dzielenie przez normę równą zero byłoby matematycznie nieokreślone.

### `semantic_search()`

Funkcja wykonuje następujący proces:

```text
embedding pytania
    -> porównanie z każdym fragmentem
    -> SemanticSearchResult
    -> sortowanie
    -> top-k
```

Każdy fragment jest oceniany niezależnie:

```python
score = cosine_similarity(query_embedding, embedded_chunk.embedding)
```

Wyniki są sortowane malejąco według score. Przy remisie używana jest ścieżka i
indeks fragmentu, więc kolejność jest deterministyczna.

Wartości zerowe i ujemne nie są usuwane przez samą funkcję. Jej zadaniem jest
ranking. Ewentualny próg istotności należy do wyższej warstwy aplikacji.

### Koszt obliczeniowy

Ta implementacja porównuje pytanie kolejno ze wszystkimi fragmentami. Dla `n`
fragmentów o wymiarze `d` wykonuje w przybliżeniu `n * d` operacji.

Jest to wystarczające dla małej kolekcji. Przy milionach wektorów stosuje się
bazy wektorowe i algorytmy approximate nearest neighbors.

### Pytania rekrutacyjne

- Co mierzy cosine similarity?
- Jak oblicza się iloczyn skalarny i normę wektora?
- Dlaczego wektory muszą mieć ten sam wymiar?
- Dlaczego zerowy wektor jest problemem?
- Czy score `0.8` oznacza 80% pewności?
- Czym wyszukiwanie semantyczne różni się od tekstowego?
- Jaka jest złożoność przeszukiwania wszystkich wektorów?
- Po co używać deterministycznego tie-breakera?

### Keywords

- **Semantic search** — wyszukiwanie na podstawie podobieństwa znaczenia.
- **Cosine similarity** — miara podobieństwa kierunku dwóch wektorów.
- **Iloczyn skalarny** — suma iloczynów wartości z odpowiadających pozycji.
- **Norma wektora** — jego matematyczna długość.
- **Zerowy wektor** — wektor zawierający same zera i mający normę zero.
- **Score podobieństwa** — liczba używana do uporządkowania wyników.
- **Top-k** — `k` wyników z najwyższym score.
- **Query embedding** — embedding pytania użytkownika.
- **Ranking** — sortowanie kandydatów według oceny dopasowania.
- **Generator expression** — leniwe generowanie kolejnych wartości w iteracji.
- **Złożoność obliczeniowa** — opis wzrostu kosztu wraz z rozmiarem danych.
- **Nearest neighbor** — element znajdujący się najbliżej zapytania w przestrzeni.
- **ANN** — approximate nearest neighbors, przybliżone wyszukiwanie sąsiadów.

---

## Ticket 9: generowanie odpowiedzi z kontekstu

### Cel

Ticket 9 dodał model językowy, który otrzymuje pytanie oraz fragmenty znalezione
przez wyszukiwarkę i tworzy na ich podstawie naturalną odpowiedź.

Ten etap znajduje się w `knowledge_assistant/generation.py`.

### Formatowanie kontekstu

`format_context()` zamienia wyniki wyszukiwania na tekst:

```text
[SOURCE: documents/python.md#chunk-1]
Treść fragmentu
[/SOURCE]
```

Identyfikator źródła składa się ze ścieżki dokumentu i indeksu fragmentu.
Pozwala modelowi rozróżnić, skąd pochodzi każda informacja.

Score nie jest przekazywany do modelu. Ranking został już wykonany, a score nie
jest dowodem prawdziwości treści.

### `instructions` i `input`

Request używa dwóch osobnych elementów:

```python
response = client.responses.create(
    model=GENERATION_MODEL,
    instructions=GENERATION_INSTRUCTIONS,
    input=user_input,
    max_output_tokens=400,
)
```

`instructions` opisuje stałe zasady zachowania modelu, np. korzystanie wyłącznie
z kontekstu i reakcję na brak danych.

`input` zawiera dane konkretnego requestu:

```text
QUESTION:
<pytanie>

CONTEXT:
<znalezione fragmenty>
```

Rozdzielenie tych części pomaga odróżnić zasady aplikacji od danych użytkownika.

### Grounding

Grounding oznacza ograniczenie odpowiedzi do dostarczonych źródeł. Model ma:

- odpowiadać na podstawie kontekstu,
- nie uzupełniać braków własną wiedzą,
- poinformować o braku wystarczających danych,
- używać wyłącznie dostępnych identyfikatorów źródeł.

Grounding zmniejsza ryzyko halucynacji, ale nie daje stuprocentowej gwarancji.
Model nadal może źle zinterpretować fragment albo nie zastosować się idealnie
do instrukcji. Dlatego zachowanie trzeba testować za pomocą evals.

### Dokument jako dane, a nie instrukcja

Treść dokumentu może zawierać zdanie wyglądające jak polecenie, np. „zignoruj
poprzednie zasady”. Model powinien traktować je jako dane, a nie polecenie.

Jest to podstawowa ochrona przed prompt injection, ale sama instrukcja nie
wystarcza do zabezpieczenia systemu produkcyjnego.

### Responses API

Projekt używa `client.responses.create()`. Odpowiedź tekstowa jest odczytywana
przez wygodną właściwość:

```python
answer = response.output_text.strip()
```

Nie trzeba ręcznie przechodzić po zagnieżdżonej strukturze `response.output`.

`max_output_tokens=400` ogranicza maksymalny budżet odpowiedzi. Limit obejmuje
tokeny generowane przez model, a nie liczbę znaków lub słów.

### Walidacja

Funkcja odrzuca:

- pytanie puste po `strip()`,
- pustą listę wyników,
- pusty tekst odpowiedzi modelu.

Niepoprawne dane wejściowe powodują `ValueError`, a nieoczekiwanie pusty wynik
modelu powoduje `RuntimeError`.

### Cytowania

Instrukcja prosi model o umieszczanie identyfikatora po twierdzeniu:

```text
Python jest używany w analizie danych.
[documents/python.md#chunk-1]
```

Na tym etapie cytowania są zwykłym tekstem wygenerowanym przez model. Aplikacja
ich nie parsuje i nie może zakładać, że zawsze są poprawne.

### Pytania rekrutacyjne

- Czym różnią się `instructions` i `input`?
- Co oznacza grounding?
- Czy grounding całkowicie usuwa halucynacje?
- Dlaczego score retrievalu nie musi trafiać do promptu?
- Dlaczego dokumenty trzeba traktować jako dane?
- Czym jest prompt injection?
- Po co ograniczać liczbę tokenów odpowiedzi?
- Dlaczego warto użyć `response.output_text`?

### Keywords

- **LLM** — duży model językowy generujący lub przetwarzający tekst.
- **Generowanie** — tworzenie nowej odpowiedzi przez model.
- **Prompt** — dane i instrukcje przekazane modelowi.
- **System/developer instructions** — nadrzędne zasady zachowania modelu.
- **Input** — dane konkretnego wywołania, np. pytanie i kontekst.
- **Context** — informacje udostępnione modelowi podczas danego requestu.
- **Grounding** — oparcie odpowiedzi na dostarczonych źródłach.
- **Halucynacja** — wygenerowanie informacji bez odpowiedniego pokrycia w danych.
- **Prompt injection** — próba zmiany zachowania modelu przez treść wejściową.
- **Responses API** — API OpenAI służące do generowania odpowiedzi modelu.
- **Output text** — tekstowa część odpowiedzi modelu.
- **Token** — jednostka tekstu przetwarzana przez model.
- **Citation** — wskazanie źródła wspierającego twierdzenie.

---

## Ticket 10: pełny przepływ RAG

### Cel

Ticket 10 połączył wcześniej niezależne elementy w jeden przepływ odpowiadania
na pytania.

```text
pytanie
  -> wczytanie i podział dokumentów
  -> embeddingi fragmentów
  -> embedding pytania
  -> wyszukiwanie semantyczne
  -> generowanie odpowiedzi
  -> odpowiedź i źródła
```

### Czym jest RAG

RAG oznacza Retrieval-Augmented Generation. System najpierw wyszukuje dane, a
dopiero później przekazuje je do modelu generującego.

Składa się z dwóch głównych części:

```text
Retrieval  -> znalezienie właściwego kontekstu
Generation -> napisanie odpowiedzi na podstawie kontekstu
```

LLM nie zna automatycznie naszych lokalnych plików. Fragmenty muszą zostać
odnalezione i jawnie przekazane w requeście.

### Model `RagAnswer`

```python
@dataclass
class RagAnswer:
    text: str
    sources: list[SemanticSearchResult]
```

Model rozdziela:

- tekst wygenerowany przez LLM,
- rzeczywiste wyniki zwrócone przez retrieval.

To ważne, ponieważ cytowania napisane przez model są generowanym tekstem.
Lista `sources` pochodzi bezpośrednio z kodu i jest bardziej wiarygodnym zapisem
tego, jakie fragmenty rzeczywiście przekazano do modelu.

### `answer_question()` jako orkiestrator

Funkcja w `rag.py` nie kopiuje algorytmów niższych warstw. Łączy istniejące
funkcje:

```text
load_or_create_embeddings()
create_embeddings()
semantic_search()
generate_answer()
```

Taka funkcja jest orkiestratorem: określa kolejność kroków i przekazuje dane
pomiędzy nimi.

### Dlaczego pytanie również potrzebuje embeddingu

Cosine similarity porównuje dwa wektory, dlatego pytanie i fragmenty muszą być
przedstawione w tej samej przestrzeni embeddingowej.

```text
tekst pytania  -> model embeddingowy -> query embedding
tekst fragmentu -> ten sam model      -> chunk embedding
```

Nie należy porównywać embeddingów utworzonych przez różne modele lub przy
niezgodnej liczbie wymiarów.

### Retrieval przed generation

Model generujący nie otrzymuje wszystkich dokumentów. Dostaje tylko kilka
najlepiej ocenionych fragmentów. Pozwala to:

- zmniejszyć ilość kontekstu,
- obniżyć koszt wejścia,
- ograniczyć nieistotne informacje,
- łatwiej wskazać źródła odpowiedzi.

Jeśli retrieval wybierze niewłaściwe fragmenty, generation może nie być w stanie
udzielić dobrej odpowiedzi. Jakość całego RAG zależy więc od obu etapów.

### Liczba requestów

Podstawowa wersja wykonywała trzy requesty:

```text
1. embeddingi fragmentów dokumentów
2. embedding pytania
3. wygenerowanie odpowiedzi
```

Późniejszy cache pozwolił pominąć pierwszy request, gdy dokumenty się nie
zmieniły. Embedding pytania i generowanie odpowiedzi nadal są wykonywane.

### Brak wiedzy

Jeżeli znaleziony kontekst nie jest wystarczający, system powinien zwrócić
ustalony komunikat zamiast zachęcać model do zgadywania.

W obecnej wersji wyższa warstwa może również odrzucać wyniki poniżej minimalnego
score. Trzeba pamiętać, że próg podobieństwa jest parametrem wymagającym
sprawdzenia na rzeczywistym zestawie pytań.

Zbyt wysoki próg odrzuci poprawne wyniki. Zbyt niski przepuści fragmenty
niezwiązane z pytaniem.

### Rola `main.py`

`main.py` powinien być cienkim punktem wejścia. Jego zadania to:

- odebranie pytania z terminala,
- przygotowanie dokumentów i klienta,
- wywołanie `answer_question()`,
- wyświetlenie odpowiedzi oraz źródeł.

Logika embeddingów, wyszukiwania i generowania pozostaje w osobnych modułach.

### Co RAG daje w porównaniu z samym LLM

- Pozwala korzystać z prywatnych lub lokalnych danych.
- Wiedzę można zaktualizować przez zmianę dokumentów.
- Nie trzeba trenować modelu po każdej zmianie informacji.
- Można pokazać użytkownikowi źródła.
- Można kontrolować zakres danych dostępnych w danym requeście.

RAG nie gwarantuje jednak poprawnej odpowiedzi. Możliwe błędy to między innymi:

- niewłaściwy podział dokumentów,
- brak właściwego fragmentu w top-k,
- błędny ranking,
- zła interpretacja kontekstu przez LLM,
- niepoprawne lub wymyślone cytowanie.

### Pytania rekrutacyjne

- Co oznacza skrót RAG?
- Z jakich etapów składa się RAG?
- Dlaczego pytanie potrzebuje embeddingu?
- Dlaczego retrieval wykonujemy przed generation?
- Czy RAG jest tym samym co fine-tuning?
- Co się stanie, jeśli retrieval zwróci zły kontekst?
- Dlaczego źródła należy przechowywać poza tekstem modelu?
- Ile requestów wykonuje podstawowy przepływ?
- Jakie są główne miejsca możliwej awarii jakości RAG?

### Keywords

- **RAG** — generowanie odpowiedzi rozszerzone o wcześniej wyszukany kontekst.
- **Retrieval** — etap wyszukiwania informacji istotnych dla pytania.
- **Generation** — etap tworzenia odpowiedzi przez model językowy.
- **Retriever** — komponent wybierający pasujące dokumenty lub fragmenty.
- **Knowledge base** — zbiór danych, z którego system pobiera wiedzę.
- **Query** — pytanie lub zapytanie użytkownika.
- **Query embedding** — wektorowa reprezentacja zapytania.
- **Retrieved context** — fragmenty znalezione i przekazane do modelu.
- **Orkiestrator** — funkcja lub komponent łączący kolejne kroki procesu.
- **Source of truth** — dane uznawane przez system za właściwe źródło informacji.
- **Similarity threshold** — minimalny score wymagany do uznania wyniku.
- **Top-k retrieval** — wybór `k` najwyżej ocenionych fragmentów.
- **End-to-end flow** — kompletny przepływ od danych wejściowych do wyniku.
- **Fallback** — bezpieczna odpowiedź używana, gdy brakuje danych.

### Dalsza lektura

- [Dokumentacja modelu `text-embedding-3-small`](https://developers.openai.com/api/docs/models/text-embedding-3-small)
- [Dokumentacja Responses API](https://developers.openai.com/api/reference/cli/resources/responses/methods/create)
- [Dokumentacja projektów `uv`](https://docs.astral.sh/uv/guides/projects/)

---

## Ticket 11: cache embeddingów dokumentów na dysku

### Po co powstał cache?

Embeddingi dokumentów nie zmieniają się przy każdym pytaniu użytkownika. Bez cache aplikacja przy każdym uruchomieniu ponownie wysyłałaby wszystkie fragmenty do OpenAI API.

Powodowałoby to:

- dłuższy czas odpowiedzi,
- dodatkowe requesty,
- większe koszty,
- niepotrzebne przetwarzanie tych samych danych.

Cache zapisuje embeddingi fragmentów w pliku JSON. Przy następnym uruchomieniu aplikacja może je odczytać zamiast ponownie generować.

Pytanie nadal wymaga nowego embeddingu, ponieważ za każdym razem może być inne.

### Cache hit i cache miss

Funkcja `load_or_create_embeddings()` ma dwa możliwe przebiegi.

**Cache hit** oznacza, że zapisany cache pasuje do aktualnych danych:

1. aplikacja odczytuje embeddingi z pliku,
2. łączy je z aktualnymi fragmentami,
3. nie wywołuje API dla dokumentów.

**Cache miss** oznacza, że cache nie istnieje albo jest nieaktualny lub uszkodzony:

1. aplikacja generuje embeddingi przez API,
2. zapisuje je na dysku,
3. zwraca nowo utworzone obiekty `EmbeddedChunk`.

Można to uprościć do:

```text
czy cache jest poprawny?
├── tak  -> użyj zapisanych embeddingów
└── nie  -> wygeneruj embeddingi i zapisz cache
```

### Fingerprint danych

Sama obecność pliku cache nie wystarcza. Dokumenty mogły zostać zmienione od czasu jego utworzenia.

Funkcja `_create_fingerprint()` buduje dane zawierające:

- nazwę modelu embeddingowego,
- liczbę wymiarów embeddingu,
- ścieżkę każdego dokumentu,
- indeks każdego fragmentu,
- treść każdego fragmentu.

Dane są serializowane do stabilnego JSON-a, a następnie przetwarzane przez SHA-256:

```python
hashlib.sha256(serialized_data.encode("utf-8")).hexdigest()
```

Wynikiem jest krótki identyfikator opisujący konkretny stan dokumentów i konfiguracji embeddingów.

Jeżeli zmieni się choć jeden fragment, model albo liczba wymiarów, fingerprint będzie inny. Stary cache zostanie wtedy potraktowany jako nieaktualny.

Fingerprint nie służy tutaj do bezpieczeństwa ani szyfrowania. Jest używany do wykrywania zmian.

### Dlaczego serializacja musi być stabilna?

Te same dane powinny zawsze tworzyć dokładnie ten sam fingerprint. Dlatego kolejność fragmentów jest zachowana, a sposób zapisu JSON-a jest określony.

Gdyby logicznie identyczne dane były za każdym razem serializowane inaczej, hash również byłby inny i cache niepotrzebnie traciłby ważność.

### Co znajduje się w pliku cache?

Plik zawiera:

- `model` — model użyty do wygenerowania embeddingów,
- `dimensions` — oczekiwaną długość wektora,
- `fingerprint` — identyfikator aktualnych danych,
- `embeddings` — listę wektorów.

Fragmenty nie są odtwarzane z cache. Program ponownie wczytuje dokumenty i tworzy chunki, a następnie łączy je z zapisanymi embeddingami za pomocą `zip(..., strict=True)`.

Dzięki temu aktualne obiekty `DocumentChunk` pozostają źródłem ścieżki, indeksu i treści.

### Walidacja cache

Plik na dysku jest zewnętrznym wejściem programu, dlatego nie można zakładać, że ma poprawny format.

Loader sprawdza między innymi:

- czy JSON można odczytać,
- czy główny element jest słownikiem,
- czy model i liczba wymiarów się zgadzają,
- czy fingerprint się zgadza,
- czy liczba embeddingów odpowiada liczbie fragmentów,
- czy każdy embedding jest listą odpowiedniej długości,
- czy każda wartość jest skończoną liczbą.

`bool` jest odrzucany osobno, ponieważ w Pythonie `bool` jest podtypem `int`. Bez dodatkowego warunku wartości `True` i `False` przeszłyby sprawdzenie liczbowe.

`math.isfinite()` odrzuca `NaN`, dodatnią nieskończoność i ujemną nieskończoność.

### Uszkodzony cache

Błąd odczytu, niepoprawny JSON lub niezgodna struktura nie kończą aplikacji. Funkcja zwraca `None`, co oznacza cache miss. Program regeneruje wtedy embeddingi.

To rozsądne zachowanie, ponieważ cache jest tylko optymalizacją. Źródłem prawdy są dokumenty, a cache można odbudować.

Błąd zapisu cache jest inną sytuacją. Jest zgłaszany wyżej jako `OSError`, ponieważ aplikacja nie powinna udawać, że pełna operacja się udała.

### Koszt i ograniczenia tego rozwiązania

Plik JSON jest prosty i czytelny, ale nie jest dobrym rozwiązaniem dla bardzo dużych zbiorów:

- cały plik jest ładowany do pamięci,
- zapisuje się cały cache naraz,
- wyszukiwanie nadal porównuje zapytanie ze wszystkimi wektorami,
- nie ma obsługi równoczesnego zapisu przez wiele procesów,
- nie ma wyszukiwania indeksowanego jak w bazie wektorowej.

Dla małego projektu edukacyjnego jest to jednak prosty i wystarczający etap pośredni.

### Pytania rekrutacyjne

- Po co cache'ować embeddingi dokumentów?
- Czym różni się cache hit od cache miss?
- Dlaczego embedding pytania nadal jest generowany przy każdym zapytaniu?
- Co powinno unieważniać cache embeddingów?
- Do czego służy fingerprint?
- Dlaczego uszkodzony cache można bezpiecznie odbudować?
- Dlaczego dane odczytane z JSON-a trzeba walidować?
- Dlaczego w tym miejscu sprawdzamy `math.isfinite()`?
- Jakie ograniczenia ma cache oparty na jednym pliku JSON?

### Keywords

- **Cache** — pomocniczy zapis danych, który pozwala uniknąć ponownego wykonywania kosztownej operacji.
- **Cache hit** — sytuacja, w której znaleziony cache jest aktualny i można go użyć.
- **Cache miss** — sytuacja, w której cache nie istnieje albo nie nadaje się do użycia.
- **Cache invalidation** — rozpoznanie, że zapisane dane są już nieaktualne.
- **Fingerprint** — skrót reprezentujący konkretny stan danych i konfiguracji.
- **Hash** — wynik funkcji skrótu obliczony na podstawie danych wejściowych.
- **SHA-256** — kryptograficzna funkcja skrótu; tutaj służy do wykrywania zmian.
- **Serialization** — zamiana danych na format możliwy do zapisania, na przykład JSON.
- **Deserialization** — odtworzenie danych programu z zapisanego formatu.
- **Source of truth** — właściwe źródło danych; tutaj są nim dokumenty, a nie cache.
- **Finite number** — liczba, która nie jest `NaN` ani nieskończonością.
- **Cache rebuild** — ponowne wygenerowanie cache, gdy stary zapis jest niepoprawny.

---

## Ticket 12: obsługa błędów API i kodów wyjścia CLI

### Dlaczego obsługujemy błędy w `main.py`?

Moduły domenowe zgłaszają wyjątki, a `main.py` znajduje się na granicy aplikacji. To właśnie tam wyjątek jest zamieniany na komunikat zrozumiały dla użytkownika i odpowiedni kod wyjścia.

Dzięki temu niższe funkcje nie muszą wiedzieć, czy aplikacja działa w terminalu, serwerze HTTP czy w innym środowisku.

### Najważniejsze rodzaje błędów

Program rozróżnia kilka typowych sytuacji:

- `AuthenticationError` — brak lub odrzucenie klucza API,
- `RateLimitError` — przekroczony limit requestów lub dostępnego quota,
- `APIConnectionError` — problem z połączeniem z API,
- `APIStatusError` — API odpowiedziało błędnym statusem HTTP,
- `OpenAIError` — pozostały błąd klienta OpenAI,
- `OSError` — problem z odczytem dokumentów lub zapisem cache,
- `ValueError` z konfiguracji — niepoprawna wartość ustawienia.

Użytkownik otrzymuje krótki komunikat, bez pełnego tracebacka i szczegółów implementacji.

### Dlaczego kolejność `except` ma znaczenie?

Wyjątki tworzą hierarchię. Bardziej szczegółowy wyjątek może dziedziczyć po bardziej ogólnym.

Dlatego najpierw przechwytujemy konkretne przypadki, takie jak `AuthenticationError` i `RateLimitError`, a dopiero później ogólny `OpenAIError`.

Gdyby ogólny typ znalazł się pierwszy, przechwyciłby także bardziej szczegółowe błędy. Kod niżej nigdy by się dla nich nie wykonał, a użytkownik straciłby dokładniejszy komunikat.

### Wstępne sprawdzenie klucza API

Przed utworzeniem klienta program sprawdza:

```python
os.environ.get("OPENAI_API_KEY", "").strip()
```

To pozwala szybko wykryć brak zmiennej lub wartość złożoną wyłącznie z białych znaków, zanim powstanie request.

Samo istnienie tekstu nie dowodzi jednak, że klucz jest prawidłowy. Dlatego program nadal obsługuje `AuthenticationError`, który może zwrócić API.

### `stdout` i `stderr`

Poprawny wynik aplikacji trafia do standardowego wyjścia, czyli `stdout`.

Błędy i komunikat użycia trafiają do `stderr`:

```python
print("Error: ...", file=sys.stderr)
```

To rozdzielenie jest ważne w skryptach i automatyzacji. Można zapisać poprawny wynik do pliku, a błędy nadal zobaczyć osobno.

### Kody wyjścia

Funkcja `main()` zwraca `int`:

- `0` — sukces,
- `1` — błąd wykonania, konfiguracji, plików lub API,
- `2` — niepoprawne użycie CLI, na przykład brak pytania.

Kod wyjścia jest informacją dla powłoki i innych programów. Nie jest tym samym co tekst wypisany w terminalu.

Na końcu programu znajduje się:

```python
if __name__ == "__main__":
    sys.exit(main())
```

`main()` zwraca liczbę, a `sys.exit()` ustawia ją jako kod zakończenia procesu.

W terminalu kod ostatniego polecenia można sprawdzić przez:

```bash
echo $?
```

### Dlaczego `main()` zwraca kod zamiast wszędzie wywoływać `sys.exit()`?

Taka funkcja jest łatwiejsza do testowania. Test może zwyczajnie wykonać `exit_code = main()` i sprawdzić wynik bez przerywania procesu testowego wyjątkiem `SystemExit`.

`sys.exit()` pozostaje tylko w prawdziwym punkcie wejścia aplikacji.

### Jak dużo informacji pokazywać użytkownikowi?

Komunikat CLI powinien być użyteczny, ale nie powinien ujawniać sekretów ani niepotrzebnych szczegółów. Nie należy wypisywać klucza API.

W systemie produkcyjnym pełne szczegóły techniczne zwykle trafiają do bezpiecznych logów, a użytkownik dostaje krótki komunikat. Ten projekt nie ma jeszcze osobnej warstwy logowania.

### Pytania rekrutacyjne

- Dlaczego wyjątki są obsługiwane na granicy aplikacji?
- Dlaczego kolejność bloków `except` jest ważna?
- Czym różni się `APIConnectionError` od `APIStatusError`?
- Dlaczego samo sprawdzenie obecności klucza API nie wystarcza?
- Czym różni się `stdout` od `stderr`?
- Co oznaczają kody wyjścia `0`, `1` i `2`?
- Dlaczego `main()` zwraca kod, a `sys.exit()` jest wywoływany dopiero na końcu?
- Dlaczego nie należy wyświetlać użytkownikowi sekretów i pełnych danych błędu?

### Keywords

- **Exception** — obiekt informujący o błędzie lub nietypowej sytuacji podczas działania programu.
- **Exception hierarchy** — relacja dziedziczenia między bardziej szczegółowymi i ogólnymi wyjątkami.
- **Error handling** — przechwytywanie błędów i świadome decydowanie, jak aplikacja ma zareagować.
- **API error** — błąd związany z komunikacją z zewnętrznym API lub jego odpowiedzią.
- **Authentication error** — błąd uwierzytelnienia, na przykład niepoprawny klucz API.
- **Rate limit** — ograniczenie liczby requestów lub dostępnego użycia API.
- **Connection error** — błąd połączenia sieciowego z usługą.
- **HTTP status error** — odpowiedź serwera z kodem oznaczającym niepowodzenie.
- **Exit code** — liczba zwracana systemowi po zakończeniu procesu.
- **`stdout`** — standardowy strumień poprawnego wyjścia programu.
- **`stderr`** — standardowy strumień komunikatów o błędach.
- **CLI boundary** — miejsce, w którym logika aplikacji komunikuje się z użytkownikiem terminala.
- **Traceback** — techniczny zapis kolejnych wywołań prowadzących do wyjątku.

---

## Ticket 13: testy jednostkowe bez prawdziwych requestów API

### Po co są testy jednostkowe?

Test jednostkowy sprawdza mały, określony fragment zachowania programu. Powinien być szybki, powtarzalny i niezależny od sieci oraz zewnętrznych usług.

W tym projekcie testy sprawdzają między innymi:

- walidację argumentów RAG,
- cache hit i cache miss,
- unieważnianie uszkodzonego cache,
- obsługę błędów w CLI,
- format odpowiedzi i źródeł,
- konfigurację domyślną i wartości z env.

### Dlaczego testy nie wykonują prawdziwych requestów?

Test zależny od OpenAI API byłby:

- wolniejszy,
- płatny,
- zależny od internetu i dostępności usługi,
- zależny od klucza API,
- mniej deterministyczny,
- trudniejszy do uruchamiania w CI.

Test jednostkowy powinien kontrolować odpowiedź zewnętrznej zależności. Prawdziwe API można sprawdzać osobnymi testami integracyjnymi, ale nie są one częścią tego ticketu.

### `Mock`

`Mock` z `unittest.mock` jest obiektem udającym prawdziwą zależność.

Może:

- zwracać przygotowaną wartość przez `return_value`,
- zgłaszać wyjątek przez `side_effect`,
- zapamiętywać wywołania,
- pozwalać sprawdzić argumenty wywołania.

Przykład:

```python
embed_chunks_mock = Mock(return_value=expected)
```

Test nie generuje embeddingów. Od razu dostaje kontrolowany wynik `expected`.

Możemy później sprawdzić:

```python
embed_chunks_mock.assert_called_once()
```

To pozwala udowodnić na przykład, że cache hit nie wykonał drugiego generowania embeddingów.

### `monkeypatch`

Fixture `monkeypatch` z pytest tymczasowo zmienia element środowiska testu.

W projekcie służy do:

- podmieniania funkcji na mock,
- zmiany `sys.argv`,
- ustawiania zmiennych środowiskowych,
- usuwania zmiennych środowiskowych.

Przykład:

```python
monkeypatch.setattr(embedding_cache, "embed_chunks", embed_chunks_mock)
```

Po zakończeniu testu pytest automatycznie cofa zmianę.

### Patchuj symbol w miejscu użycia

Mock należy zwykle wstawić tam, gdzie testowany moduł wyszukuje daną nazwę.

`embedding_cache.py` importuje `embed_chunks`, dlatego test podmienia:

```python
embedding_cache.embed_chunks
```

a nie definicję w oryginalnym module `embeddings`.

To częsta pułapka podczas korzystania z mocków w Pythonie.

### `tmp_path`

`tmp_path` daje testowi tymczasowy katalog jako obiekt `Path`.

Jest używany do testowania plików cache bez zapisywania danych w prawdziwym katalogu projektu:

```python
cache_path = tmp_path / "embeddings.json"
```

Każdy test otrzymuje odizolowane miejsce, które pytest później sprząta.

### `capsys`

`capsys` przechwytuje dane wypisane do `stdout` i `stderr`.

Po wykonaniu `main()` test może sprawdzić:

```python
captured = capsys.readouterr()
```

- `captured.out` zawiera `stdout`,
- `captured.err` zawiera `stderr`.

Dzięki temu można sprawdzić zarówno komunikat CLI, jak i to, czy trafił do właściwego strumienia.

### `pytest.raises`

`pytest.raises` sprawdza, czy kod zgłosił oczekiwany wyjątek:

```python
with pytest.raises(ValueError, match="expected message"):
    load_config()
```

Testuje zarówno typ wyjątku, jak i opcjonalnie jego komunikat.

### Parametryzacja

`@pytest.mark.parametrize` pozwala uruchomić ten sam test dla wielu danych wejściowych.

Zamiast tworzyć osobny test dla `0` i `-1`, można użyć jednego testu z dwiema wartościami. Zmniejsza to duplikację i jasno pokazuje zestaw sprawdzanych przypadków.

### Schemat Arrange–Act–Assert

Czytelny test często składa się z trzech etapów:

1. **Arrange** — przygotuj dane, mocki i środowisko.
2. **Act** — wykonaj testowaną funkcję.
3. **Assert** — sprawdź wynik i efekty uboczne.

Test powinien mówić, jakie zachowanie jest wymagane, a nie powtarzać wewnętrzną implementację funkcji.

### Unit test a integration test

Unit test izoluje badaną jednostkę i zastępuje zewnętrzne zależności.

Integration test sprawdza współpracę kilku prawdziwych komponentów, na przykład kodu z rzeczywistym API albo bazą danych.

Mocków nie należy używać wszędzie. Nadmierne mockowanie może sprawić, że test sprawdza własne założenia, a nie działanie systemu.

### Zależność developerska

`pytest` znajduje się w grupie zależności deweloperskich:

```toml
[dependency-groups]
dev = [
    "pytest>=9.1.1",
]
```

Jest potrzebny do rozwoju projektu, ale nie do działania aplikacji dla użytkownika.

Testy uruchamiamy przez:

```bash
uv run pytest
```

### Pytania rekrutacyjne

- Czym jest test jednostkowy?
- Dlaczego unit test nie powinien wykonywać prawdziwych requestów API?
- Czym różni się mock od prawdziwego obiektu?
- Do czego służą `return_value` i `side_effect`?
- Co robi `monkeypatch`?
- Dlaczego mockujemy symbol w miejscu jego użycia?
- Do czego służą fixtures `tmp_path` i `capsys`?
- Co sprawdza `pytest.raises`?
- Kiedy warto użyć parametryzacji?
- Czym różni się unit test od integration test?
- Jakie ryzyko niesie nadmierne mockowanie?

### Keywords

- **Unit test** — szybki test małego fragmentu zachowania programu w izolacji.
- **Integration test** — test sprawdzający współpracę kilku prawdziwych komponentów.
- **Test double** — ogólna nazwa obiektu zastępującego prawdziwą zależność w teście.
- **Mock** — test double, który może zwracać wyniki i rejestrować wywołania.
- **Stub** — prosta zastępcza implementacja zwracająca przygotowane dane.
- **Fixture** — dane lub zasób przygotowywany dla testu przez pytest.
- **`monkeypatch`** — fixture do tymczasowej zmiany obiektów, argumentów lub środowiska.
- **`tmp_path`** — fixture udostępniająca izolowany katalog tymczasowy.
- **`capsys`** — fixture przechwytująca `stdout` i `stderr`.
- **Assertion** — sprawdzenie, czy rzeczywisty wynik zgadza się z oczekiwaniem.
- **`return_value`** — wartość zwracana przez mock po jego wywołaniu.
- **`side_effect`** — dodatkowe zachowanie mocka, na przykład zgłoszenie wyjątku.
- **Parametrization** — uruchomienie jednego testu dla wielu zestawów danych.
- **Deterministic test** — test, który dla tych samych warunków zawsze daje ten sam wynik.
- **CI** — automatyczne środowisko uruchamiające między innymi testy po zmianach w kodzie.

---

## Ticket 14: konfiguracja operacyjna przez zmienne środowiskowe

### Czym jest konfiguracja operacyjna?

Są to ustawienia, które mogą zmieniać się między środowiskami lub uruchomieniami, ale nie powinny wymagać edycji kodu.

W projekcie są to:

- katalog dokumentów,
- ścieżka cache,
- maksymalna liczba wyników,
- minimalny próg podobieństwa.

Zmienne środowiskowe pozwalają uruchamiać ten sam kod z innymi ustawieniami lokalnie, w CI, Dockerze lub na serwerze.

### Obsługiwane zmienne

Projekt odczytuje:

- `KNOWLEDGE_DOCUMENTS_DIR` — katalog z dokumentami, domyślnie `documents`,
- `KNOWLEDGE_CACHE_PATH` — ścieżkę cache, domyślnie `.cache/embeddings.json`,
- `KNOWLEDGE_RESULT_LIMIT` — liczbę wyników, domyślnie `3`,
- `KNOWLEDGE_MIN_SIMILARITY_SCORE` — minimalny score, domyślnie `0.5`.

Przykład jednorazowego uruchomienia:

```bash
KNOWLEDGE_RESULT_LIMIT=5 \
KNOWLEDGE_MIN_SIMILARITY_SCORE=0.65 \
uv run python main.py "What are embeddings?"
```

### Model `AppConfig`

Po odczytaniu i sprawdzeniu wartości funkcja `load_config()` zwraca jeden obiekt:

```python
@dataclass(frozen=True)
class AppConfig:
    documents_directory: Path
    cache_path: Path
    result_limit: int
    min_similarity_score: float
```

Zalety takiego modelu:

- konfiguracja ma jawne typy,
- wszystkie ustawienia są zebrane w jednym miejscu,
- nie trzeba wielokrotnie odczytywać `os.environ`,
- łatwo przekazać konfigurację do dalszych funkcji,
- łatwo utworzyć kontrolowaną konfigurację w teście.

`frozen=True` blokuje zwykłą zmianę pól po utworzeniu obiektu. Konfiguracja staje się w praktyce niezmienna podczas działania programu.

### Dlaczego potrzebne jest parsowanie?

Zmienne środowiskowe są tekstem. Nawet wartość `5` jest początkowo napisem `"5"`.

Dlatego loader wykonuje konwersję:

```python
result_limit = int(result_limit_value)
min_similarity_score = float(min_similarity_score_value)
```

Bez tego typy nie zgadzałyby się z polami `AppConfig`, a porównania liczbowe mogłyby działać niepoprawnie.

### Walidacja konfiguracji

Program sprawdza konfigurację przed tworzeniem klienta i wykonywaniem requestów:

- ścieżki po `strip()` nie mogą być puste,
- limit musi być liczbą całkowitą większą od zera,
- próg podobieństwa musi być liczbą,
- próg musi mieścić się w zakresie od `-1.0` do `1.0`.

Jest to podejście nazywane **fail fast**: aplikacja kończy się od razu z czytelnym błędem zamiast działać dalej z niepoprawnymi ustawieniami.

### Domyślne wartości

Wywołanie:

```python
os.environ.get("KNOWLEDGE_RESULT_LIMIT", "3")
```

oznacza: pobierz wartość zmiennej, a jeśli nie istnieje, użyj `"3"`.

Domyślne wartości pozwalają uruchomić aplikację bez ustawiania wszystkich zmiennych. Jednocześnie środowisko może nadpisać tylko te elementy, które rzeczywiście wymagają zmiany.

### Po co `.strip()`?

`.strip()` usuwa białe znaki z początku i końca wartości. Dzięki temu:

- `" 5 "` można poprawnie zamienić na liczbę,
- `"   "` zostanie rozpoznane jako pusta wartość,
- przypadkowe spacje nie zmienią ścieżki.

### `raise ... from error`

Podczas nieudanej konwersji powstaje oryginalny `ValueError`. Loader zgłasza nowy wyjątek z komunikatem dotyczącym konkretnej zmiennej:

```python
except ValueError as error:
    raise ValueError(
        "KNOWLEDGE_RESULT_LIMIT must be a positive integer"
    ) from error
```

`from error` zachowuje informację o pierwotnej przyczynie. Użytkownik dostaje czytelny komunikat, a podczas debugowania nadal można zobaczyć łańcuch wyjątków.

### Konfiguracja a sekrety

Zmienna `OPENAI_API_KEY` również pochodzi ze środowiska, ale jest sekretem. Nie należy dodawać jej do kodu ani repozytorium.

Pozostałe ustawienia operacyjne zwykle nie są sekretami. Nadal warto trzymać je poza kodem, ponieważ różnią się między środowiskami.

Projekt ignoruje pliki `.env`, ale sam nie ładuje ich automatycznie i nie ma zależności takiej jak `python-dotenv`. Wartości trzeba przekazać przez rzeczywiste środowisko procesu.

### Wpływ progu podobieństwa

`KNOWLEDGE_MIN_SIMILARITY_SCORE` kontroluje, które wyniki retrievalu trafią do generatora:

- niższy próg zwiększa liczbę dopuszczonych fragmentów, ale może dodać słabszy kontekst,
- wyższy próg jest bardziej restrykcyjny, ale może odrzucić przydatny fragment.

Nie istnieje jedna idealna wartość dla każdego zbioru danych. Próg powinien być dobierany na podstawie ewaluacji.

### Pytania rekrutacyjne

- Dlaczego konfigurację operacyjną oddzielamy od kodu?
- Jakie wartości zwraca `os.environ.get()`?
- Dlaczego zmienne liczbowe trzeba jawnie parsować?
- Co daje centralny model `AppConfig`?
- Co oznacza `frozen=True` w dataclass?
- Na czym polega podejście fail fast?
- Po co są wartości domyślne?
- Co robi `raise ... from error`?
- Czym różni się zwykła konfiguracja od sekretu?
- Czy Python automatycznie ładuje plik `.env`?
- Jak próg podobieństwa wpływa na precision i recall retrievalu?

### Keywords

- **Configuration** — ustawienia wpływające na działanie programu bez zmiany jego logiki.
- **Environment variable** — nazwana wartość tekstowa przekazana procesowi przez środowisko.
- **Operational configuration** — ustawienia zmieniane zależnie od sposobu lub miejsca uruchomienia.
- **Default value** — wartość używana, gdy użytkownik nie poda własnej.
- **Parsing** — zamiana tekstu na właściwy typ, na przykład `int` lub `float`.
- **Validation** — sprawdzanie, czy wartość spełnia wymagania programu.
- **Fail fast** — przerwanie działania możliwie wcześnie po wykryciu błędnych danych.
- **Immutable configuration** — konfiguracja, której nie zmienia się po utworzeniu.
- **Secret** — poufna wartość, na przykład klucz API, której nie wolno zapisywać w repozytorium.
- **`.env` file** — popularny plik z wartościami środowiskowymi; Python nie ładuje go samoczynnie.
- **Exception chaining** — zachowanie związku między nowym wyjątkiem a jego pierwotną przyczyną.
- **Similarity threshold** — minimalna wartość podobieństwa wymagana do przyjęcia wyniku.
- **Precision** — część zwróconych wyników, które rzeczywiście są trafne.
- **Recall** — część wszystkich trafnych wyników, które system zdołał znaleźć.

### Dalsza lektura

- [OpenAI API reference — zmienna `OPENAI_API_KEY`](https://developers.openai.com/api/reference/python/resources/skills/methods/create)

---

## Ticket 15: ewaluacja retrievalu za pomocą Hit@k

### Po co ewaluować retrieval?

System RAG może wygenerować dobrą odpowiedź tylko wtedy, gdy wcześniej znajdzie właściwy kontekst. Dlatego retrieval warto mierzyć oddzielnie od generowania tekstu.

Ewaluacja odpowiada tutaj na pytanie:

> Czy dokument zawierający odpowiedź znalazł się wśród `k` najwyżej ocenionych wyników?

Dzięki temu można sprawdzić jakość wyszukiwania bez oceniania stylu lub poprawności odpowiedzi modelu językowego.

### Stały zestaw pytań

Plik `evaluation/questions.json` zawiera przypadki testowe. Każdy przypadek ma:

- `question` — pytanie wysyłane do wyszukiwarki,
- `expected_source` — dokument, który powinien zostać znaleziony.

Przykład:

```json
{
  "question": "Jak tekst może zostać przedstawiony jako liczby?",
  "expected_source": "documents/embeddings.md"
}
```

Taki zestaw nazywa się zbiorem ewaluacyjnym. Powinien zawierać pytania reprezentujące rzeczywiste sposoby korzystania z aplikacji.

### Modele danych

`EvaluationCase` przechowuje pojedynczy przypadek:

```python
@dataclass(frozen=True)
class EvaluationCase:
    question: str
    expected_source: Path
```

`EvaluationResult` opisuje wynik jednego pytania:

```python
@dataclass
class EvaluationResult:
    case: EvaluationCase
    retrieved_sources: list[Path]
    hit: bool
```

`EvaluationSummary` łączy wszystkie wyniki i końcową metrykę:

```python
@dataclass
class EvaluationSummary:
    results: list[EvaluationResult]
    hit_rate: float
```

Rozdzielenie modeli ułatwia późniejsze wyświetlanie raportu, zapis wyników albo porównywanie eksperymentów.

### Wczytywanie przypadków

`load_evaluation_cases()`:

1. otwiera plik JSON,
2. sprawdza, czy JSON jest poprawny,
3. wymaga niepustej listy,
4. sprawdza każdy rekord,
5. usuwa zbędne białe znaki,
6. tworzy obiekty `EvaluationCase`.

Plik jest zewnętrznym wejściem programu, dlatego jego struktury nie można uznać za poprawną bez walidacji.

### Jak działa `evaluate_retrieval()`?

Przepływ wygląda następująco:

```text
dokumenty -> chunki -> embeddingi dokumentów
                              |
pytania -> embeddingi pytań  |
             |                |
             +---- porównanie-+
                       |
                 wyniki top-k
                       |
              Hit albo Miss
```

Funkcja:

1. sprawdza argumenty,
2. ładuje lub generuje embeddingi dokumentów,
3. generuje embeddingi wszystkich pytań,
4. wykonuje wyszukiwanie dla każdego pytania,
5. zbiera ścieżki znalezionych dokumentów,
6. sprawdza obecność oczekiwanego źródła,
7. oblicza końcowy hit rate.

### Batchowanie pytań

Treści wszystkich pytań są przekazywane do `create_embeddings()` jednocześnie:

```python
question_embeddings = create_embeddings(
    client,
    [case.question for case in cases],
)
```

Dzięki temu nie wykonujemy osobnego requestu embeddingowego dla każdego pytania. Odpowiedzi są następnie łączone z przypadkami za pomocą `zip(..., strict=True)`.

Embeddingi dokumentów również nie są niepotrzebnie regenerowane, ponieważ evaluator wykorzystuje istniejący cache.

### Co oznacza Hit@k?

`k` określa liczbę najwyżej ocenionych fragmentów branych pod uwagę.

Dla `Hit@3` wynik jest pozytywny, jeśli oczekiwany dokument wystąpi wśród źródeł trzech najlepszych fragmentów.

Przykład:

```text
Expected: documents/embeddings.md

Top 3:
1. documents/vector-search.md
2. documents/embeddings.md
3. documents/rag.md
```

Wynik to `hit=True`, ponieważ oczekiwane źródło znajduje się na drugiej pozycji.

Jeśli źródła nie ma w top 3, otrzymujemy `hit=False`, czyli miss.

### Hit rate

Hit rate to udział pytań zakończonych trafieniem:

```text
hit_rate = liczba trafień / liczba wszystkich pytań
```

Jeśli cztery z pięciu pytań odnalazły właściwy dokument:

```text
Hit@3: 4/5 (80.0%)
```

Hit rate przyjmuje wartość od `0.0` do `1.0`, a CLI pokazuje ją również jako procent.

### Ewaluacja na poziomie dokumentu

Wyszukiwarka zwraca fragmenty, ale przypadek ewaluacyjny wskazuje dokument. Dlatego z wyników pobierane są ścieżki `document_path`.

Duplikaty są usuwane z zachowaniem kolejności:

```python
list(dict.fromkeys(...))
```

Jeżeli w top-k znajdą się trzy fragmenty tego samego dokumentu, w `retrieved_sources` ta ścieżka pojawi się tylko raz.

Obecna metryka sprawdza więc, czy odnaleziono właściwy dokument. Nie sprawdza, czy wybrano dokładnie właściwy fragment.

### Normalizacja ścieżek

Katalog dokumentów może zostać zmieniony przez konfigurację. Przykładowo rzeczywisty plik może mieć ścieżkę:

```text
/tmp/custom-documents/python.md
```

Zestaw ewaluacyjny nadal używa stabilnego identyfikatora:

```text
documents/python.md
```

`_canonical_source_path()` zamienia ścieżki pochodzące z różnych katalogów na wspólny, kanoniczny format. Bez tego właściwy dokument mógłby zostać błędnie oznaczony jako miss tylko dlatego, że został wczytany z innego miejsca.

### Dlaczego nie wywołujemy `generate_answer()`?

Celem ticketu jest pomiar retrievalu, a nie pełnego RAG-u. Generowanie odpowiedzi dodałoby kolejną zmienną do eksperymentu:

- retrieval mógłby znaleźć poprawne źródło, ale model źle odpowiedzieć,
- retrieval mógłby znaleźć słabe źródło, ale model przypadkiem udzielić dobrej odpowiedzi.

Oddzielne mierzenie etapów pozwala dokładniej znaleźć źródło problemu.

### Osobne CLI

Ewaluację uruchamia osobny plik:

```bash
uv run python evaluate.py
```

Nie jest ona częścią zwykłego `main.py`, ponieważ użytkownik aplikacji chce otrzymać odpowiedź, a developer chce otrzymać raport jakości.

Dla każdego przypadku CLI wypisuje:

- `PASS` albo `FAIL`,
- pytanie,
- oczekiwane źródło,
- znalezione źródła.

Na końcu pokazuje zbiorczy `Hit@k`.

Proces zwraca kod `0`, jeśli wszystkie przypadki przeszły, albo `1`, jeśli wystąpił miss lub błąd wykonania. Dzięki temu ewaluację można później wykorzystać w automatyzacji i CI.

### Ewaluacja a test jednostkowy

Test jednostkowy sprawdza, czy kod realizuje określone reguły, na przykład czy dobrze liczy hit rate.

Ewaluacja mierzy jakość zachowania systemu na zestawie danych, na przykład czy embeddingi i ranking odnajdują właściwe dokumenty.

Kod może przechodzić wszystkie testy jednostkowe, a mimo tego mieć niski Hit@k. Oznacza to, że implementacja działa zgodnie z kodem, ale jakość wyszukiwania jest słaba.

### Ograniczenia obecnej metryki

Hit@k jest prostą metryką i nie mówi wszystkiego:

- nie uwzględnia dokładnej pozycji trafienia,
- nie ocenia pozostałych znalezionych dokumentów,
- nie mierzy jakości wygenerowanej odpowiedzi,
- zależy od jakości ręcznie przygotowanych oczekiwanych źródeł,
- mały zestaw pytań może nie reprezentować prawdziwych użytkowników.

Przykładowo trafienie na pierwszym i trzecim miejscu daje ten sam `hit=True`. Metryki takie jak MRR albo NDCG potrafią uwzględnić pozycję wyniku.

### Inne metryki retrievalu

- **Precision@k** — jaki procent spośród `k` zwróconych wyników jest trafny.
- **Recall@k** — jaki procent wszystkich trafnych wyników znalazł się w top-k, przydatne gdy istnieje kilka poprawnych dokumentów.
- **MRR (Mean Reciprocal Rank)** — ocenia pozycję pierwszego trafnego wyniku; im wyżej się znajduje, tym lepszy wynik.
- **MAP (Mean Average Precision)** — ocenia pozycje wszystkich trafnych wyników i uśrednia rezultat dla wielu pytań.
- **NDCG@k** — ocenia kolejność wyników, uwzględniając ich pozycję oraz różne poziomy trafności.

Dobór metryki zależy od celu. `Hit@k` wystarcza, gdy interesuje nas samo znalezienie oczekiwanego dokumentu, natomiast MRR lub NDCG lepiej pokazują jakość kolejności wyników.

### Jak tworzyć dobry zestaw ewaluacyjny?

Warto uwzględnić:

- różne sposoby zadawania tego samego pytania,
- pytania używające innych słów niż dokument,
- pytania łatwe i trudne,
- tematy z różnych dokumentów,
- przypadki niejednoznaczne,
- pytania, na które dokumenty nie zawierają odpowiedzi.

Nie należy dostosowywać systemu tylko do kilku znanych pytań. Mogłoby to poprawić wynik zestawu ewaluacyjnego bez poprawienia jakości dla prawdziwych użytkowników.

### Pytania rekrutacyjne

- Dlaczego retrieval warto ewaluować oddzielnie od generowania odpowiedzi?
- Co oznacza Hit@k?
- Jak oblicza się hit rate?
- Jaki wpływ na wynik ma wartość `k`?
- Dlaczego pytania embeddingujemy jednym batchem?
- Dlaczego evaluator korzysta z cache embeddingów dokumentów?
- Czym różni się ewaluacja od testu jednostkowego?
- Dlaczego usuwamy powtarzające się ścieżki dokumentów?
- Po co normalizować ścieżki źródeł?
- Jakie ograniczenia ma Hit@k?
- Jak powinien wyglądać dobry zestaw ewaluacyjny?
- Dlaczego wysoki Hit@k nie gwarantuje dobrej odpowiedzi końcowej?

### Keywords

- **Evaluation** — systematyczny pomiar jakości działania systemu na przygotowanych danych.
- **Evaluation dataset** — zestaw pytań i oczekiwanych wyników używany do pomiaru jakości.
- **Retrieval evaluation** — ocena jakości etapu wyszukiwania informacji.
- **Ground truth** — ręcznie ustalony oczekiwany wynik używany jako punkt odniesienia.
- **Hit** — przypadek, w którym oczekiwane źródło znalazło się w top-k.
- **Miss** — przypadek, w którym oczekiwanego źródła zabrakło w top-k.
- **Hit@k** — informacja, czy oczekiwany wynik znalazł się wśród `k` najlepszych wyników.
- **Hit rate** — liczba trafień podzielona przez liczbę wszystkich przypadków.
- **Top-k** — `k` wyników z najwyższym wynikiem podobieństwa.
- **Batching** — przetwarzanie wielu elementów w jednym wywołaniu API.
- **Canonical path** — stabilna, ujednolicona postać ścieżki używana do porównań.
- **Deduplication** — usuwanie powtarzających się elementów.
- **Metric** — liczba opisująca wybrany aspekt jakości systemu.
- **Baseline** — początkowy wynik służący jako punkt odniesienia dla kolejnych zmian.
- **Regression** — pogorszenie wcześniej działającego zachowania lub wyniku.
- **MRR** — metryka uwzględniająca pozycję pierwszego poprawnego wyniku.
- **NDCG** — metryka rankingu uwzględniająca pozycję i stopień trafności wyników.
- **Dataset leakage** — sytuacja, w której system został zbyt mocno dostrojony do znanego zestawu ewaluacyjnego.
