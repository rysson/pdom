
Nowa obsługa DOM
================

Początkujący mogą przejrzeć pewne [podstawy](podstawy.md).


Klasy i typy
============

[`Node`](dom-node.md) – opisuje węzeł HTML/XML, czyli jest to tag z zawartością.


pdom.search()
============

Funkcja parsuje HTML/XML, znajduje tagi z atrybutami
i zwraca te pasujące wraz z żądaną zawartością 
czy to tekst, atrybuty, czy węzeł Node().


pdom.select()
============

Przeszukiwanie (wybieranie) danych z HTML na wzór uproszczonych 
selektorów, podobnych do tych z CSS czy jQuery.


### Przykłady

Większość przykładów używa poniższego źródła HTML.

```python
# HTML w stylu  A ( B C ) A ( B )
html = '<a x="11" y="12">A1<b>B1</b><c>C1</c></a> <a x="21" y="22">A2<b>B2</b></a>'
```


Selektory
---------

Pierwszy z brzegu kurs, gdzie wyjaśnione są selektory CSS – http://www.kurshtml.edu.pl/css/selektory.html

Tutaj jest tylko namiastka tych możliwości ale i tak pozwala to w miarę sprawnie wyłuskiwać dane.


### Obsługiwanie selektory

Selektor     | Opis
-------------|------------
\*           | Każdy element.
\#id         | Każdy element z podanym `id`.
.class       | Każdy element z podaną klasą `class`.
tag          | Wskazany `<tag>`.
E1, E2       | Grupa, znajdywana są wszystkie E1 oraz E2 (nie można zagłębiać).
E1 E2        | Potomek, wszystkie E2 które są potomkiem E1 (czyli znajsduję się w E1).
E1 > E2      | Dziecko, wszystkie E2 które są bezpośrednim dzieckiem E1.
E1 + E2      | Brat, wszystkie E2 które są bezpośrednio za bratem E1.
[attr]       | Każdy element, który posiada atrybut `attr`.
[attr=val]   | Każdy element, z atrybutem `attr` równym `val`.
[attr^=val]  | Każdy element, z atrybutem `attr` rozpoczęty od `val`.
[attr$=val]  | Każdy element, z atrybutem `attr` zakończony na `val`.
[attr~=val]  | Każdy element, z atrybutem `attr` ze słowem¹ `val`.
[attr\|=val] | Każdy element, z atrybutem `attr` ze słowem¹ rozpoczętym od `val`.
[attr*=val]  | Każdy element, z atrybutem `attr` zawierający tekst `val`.
[attr~regex] | Każdy element, z atrybutem `attr` spełniącym wyrażenie regularne `regex` (eksperyment!).

¹) Słowo to ciąg znaków (bez spacji).


#### Przykłady

##### Pojedynczy węzeł

```python
for b in dom_select(html, 'a b'):
    print('Result:', b.text)
# Result: B1
# Result: B2
```

Łapie wszystkie tagi `b`, które są zawarte w tagu `a`.



### Dodatkowe selektory

Poniższe selektory wychodzą poza standard CSS i jQuery.

Selektor       | Opis
---------------|------------
{ E1, E2 }     | Zestaw, zarówno E1 jaki i E2.
E1?            | Opcja, E1 albo None, gdy nie istnieje.
{ E1:N, ... }  | N-te wystapienie E1 w zestawie.

Selektor zestaw zwraca podlistę i dzięki temu pozwala złapać wiele elementów,
które są zawarte w nadrzędnym za pomocą jednego zapytania. 
Jeśli któryś z elementów w selektorze zestawu jest opcjonalny, to zwrócone
zostanie None w tej samej pozycji, w której brakuje elementu.

Element opcjonalny jest użyteczny w selektorze zestawu. 
Zwracane jest None na odpowiedniej pozycji dzięki czemu łatwiej takie zapytanie
przetwarzać w pętli for.


#### Przykłady

##### Zestaw

```python
for b, c in dom_select(html, 'a {b, c}'):
    print('Result:', b.text, c.text)
# Result: B1 C1
```

Łapie tagi `b` i `c`, które są zawarte w `a`.
Złapało tylko jedną linię, bo drugi tag `a` nie posiada `c`.

##### Powtórzenia

Gdy selektor w zestawie powtarza się wyszukiwane jest kolejne wystąpienie (tutaj 2x `p`), np. dla html:

```html
<p>Tytuł</p>
<a href="http://tam/">oglądaj</a>
<p>Piękny film, który..."</p>
```

```python
for title, descr, link in dom_select(html, '{p p a}'):
    print('Film {title!r} {link.href}: {descr!r}'.format(**locals()))
```

```
Film 'Tytuł' http://tam/ 'Piękny film, który...'
```


Aby zachować stare działanie trzeba użyć `{{p p a}}`, wtedy dostajemy to w dziwnej postaci:
```
Film 'Tytuł' http://tam/ 'Tytuł'
Film 'Piękny film, który...' http://tam/ 'Piękny film, który...'
```

__Uwaga:__ stary zestaw `{{ }}` jest do usunięcia.


##### Powtórzenia numerowane

Można wybrać, które powtórzenia mają się znaleźć w wyniku.

Z przykładu wyżej selektor `{p:2}` zwróci tylko opisy filmów.

Jeśli brak numeru to użyty jest zawsze o jeden większy niż poprzednio dla takiego samego selektora, czyli:

```html
<div>
  <p>Tytuł</p>
  <p>Rok</p>
  <a href="/gatunki">Gatunek</a>
  <p>Opis</p>
  <a href="/patrz">Oglądaj</a>
</div>
```

Z `div {p, p, a:2}` daje `Tytuł` (p1), `Rok` (p2), `Oglądaj` (a2).

Z `div {p:3, p:1, p, a:2}` daje `Opis` (p3), `Tytuł` (p1), `Rok` (p2), `Oglądaj` (a2).

Z `div {p:2, a, p, a, p:1}` daje `Rok` (p2), `Gatunek` (a1), `Opis` (p3), `Oglądaj` (a2), `Tytuł` (p1).


##### Zestaw z opcją

```python
for b, c in dom_select(html, 'a {b, c?}'):
    print('Result:', b.text, c and c.text)
# Result: B1 C1
# Result: B2 None
```

Jak wyżej, łapie tagi `b` i `c`, które są zawarte w `a`, z tym, że `c` jest opcjonalny.
Pierwsza linia trafiła w `b` i `c` z pierwszego `a` (jak wyżej).
Druga linia też trafiła (w drugie `a`) tylko zwróciła `b` i None (bo nie ma tam `c`).


### Pseudo-klasy węzła

Selektor              | Opis
----------------------|------------
:contains(S)          | Łapie jeśli tekst `S` zawiera się w *tekście* węzła.
:content-contains(S)  | Łapie jeśli tekst `S` zawiera się w zawartości węzła (innerHTML).
:regex(R)             | Łapie jeśli wyrażenie regularne `R` trafi w outerHTML.
:has(T)               | Łapie jeśli węzeł posiada w zawartości tag `T`.
:empty                | Łapie tylko puste tagi (bez tekstu czy tagów w zawartości).
:first-child          | Łapie pierwszy element z rodzeństwa
:last-child           | Łapie ostatni element z rodzeństwa
:only-child           | Łapie samotny element (bez rodzeństwa), to samo co :first-child:last-child
:first-of-type        | Łapie pierwszy element z rodzeństwa tego samego typu
:last-of-type         | Łapie ostatni element z rodzeństwa tego samego typu
:only-of-type         | Łapie element bez rodzeństwa tego typu, jak :first-of-type:last-of-type
:enabled              | Łapie elementy nie wyszarzone (bez atrybutu „disabled”)
:disabled             | Łapie elementy wyszarzone (z atrybutem „disabled”)
:not(E)               | Łapie elementy, które się nie łapią w prosy selektor `E`

Powyższe pseudo-klasy są wyraźnie wolniejsze ponieważ do sprawdzenia muszą znaleźć tag zamykający.

`:has` używa uproszczonego wyszukiwania i może znaleźć tag `T` nawet w wartości atrybutu.
To zostanie naprawione. Kiedyś...


#### Przykłady

##### :contains(S)

```python
for a in dom_select(html, 'a:contains("2B2")'):
    print('Result:', a.text)
# Result: A2B2
```

##### :empty(S)

```python
for a in dom_select('<a></a><b/><c>C</c>', ':empty'):
    print('Result:', a.name)
# Result: a
# Result: b
```


### Pseudo-elementy wyniku

Selektor     | Opis
-------------|------------
::node       | Zwraca węzeł Node (domyślne dla ostatniego tagu z selektorze).
::text       | Zwraca test z węzła (bez tagów), np.  `AB`
::content    | Zwraca zawartość węzła, np. `A<b>B</b>`
::innerHTML  | Jak wyżej.
::outerHTML  | Zwraca cały węzeł (tag i zawartość), np. `<a>A<b>B</b></a>`
::attr(A)    | Zwraca atrybut `A`. Można użyć listy atrybutów rozdzielonych przecinkami.
(A)          | Skrót dla `::attr(A)`.
::none       | Nic nie zwraca. Węzeł musi istnieć.
::DomMatch   | Zwraca węzły DomMatch, dla kompatybilności.

Jeśli żaden z pseudo-element wyniku nie jest użyty, to zwracany jest Node.
Jeśli jest użyty choć jeden zwracana jest lista z żądanymi rzeczami.
Jak jest pojedynczy element to zwracany jest wprost (domyślny `flat`)
albo też jako lista (przy wymuszeniu `no-flat`).

1. `A` → `Node(A)`

2. `A::node` → `Node(A)`

3. `A(x,y)::content` → `[x, y, 'A']`

4. `A(x)` → `x`

5. `A(x)` → `[x]`  (`no-flat`)


Przy starym zachowaniu (`no-flat`) gdy pobierany jest jeden atrybut potrzeba dodatkowego wyłuskiwania. 
Poniżej porównanie przypadków 1 i 4 i wypisania atrybutu *x*.

```python
# 1.
for a in pdom.select(html, 'a'):
    print(a.x)

# 4.
for x in pdom.select(html, 'a(x)'):
    print(x)

# 5. (no-flat)
for (x,) in pdom.select(html, 'a(x)', flat=False):
    print(x)
```


#### Przykłady

##### Węzeł rodzica z dwoma potomkami (zestaw) z czego jeden opcjonalny

```python
for a, b, c in dom_select(html, 'a::node {b, c?}'):
    print('Result:', a.text b.text, c and c.text)
# Result: A1B1C1 B1 C1
# Result: A2B2 B2 None
```

Tag `a` powinien posiadać `b` i `c` i zawsze oba są zwracane. Przy czym `c` jest opcjonalne, 
czyli jeśli go nie ma, w jego miejsce zwracane jest None. 
Dodatkowe nawiasy wokół *a* są z powodu listy, co zostało wyjaśnione wyżej.

Pierwsza linia trafiła w pierwsze `a` oraz potomków `b` i `c`.
Druga linia też trafiła (w drugie `a`) tylko zwróciła `b` i None (bo nie ma tam `c`).


Stare zachowanie gdy (`flat=False`) generuje dodatkowe zagłębienia:

```python
for (a,), b, c in dom_select(html, 'a::node {b, c?}', flat=False):
    print('Result:', a.text b.text, c and c.text)
# Result: A1B1C1 B1 C1
# Result: A2B2 B2 None
```

