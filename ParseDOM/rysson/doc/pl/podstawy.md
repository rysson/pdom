# Podstawy

## HTML / XML

HTML (Hypertext Markup Language) jest to kod używany do tworzenia struktury strony i jej zawartości.
Struktura ma charakter hierarchiczny, dokładniej drzewiasty.

```html
<html>
  <style>
    <title>Jak fajna strona</title>
  </style>
  <body>
    <h1>Mój nagłówek</h1>
    <div>
      <p>Pierwszy akapit</p>
      <p>Drugi akapit – <b>grubo</b> i <i>pochyło</i></p>
    </div>
  </body>
</html>
```


## Czego szukać

pdom.search() wyszukuje nam elementy, ale opis co jest dość zagmatwany. Za to łatwo może udać starą funkcję parseDOM().

pdom.select() wybiera informacje na wzór selektorów CSS. Co to jest? Już wyjaśniam.



### Selektor

CSS (arkusze stylów) określają co jak przerobić. Jak przerobić nas tutaj nie interesuje. Co przerobić, czyli co wybrać, jak najbardziej.

Selektor, jak sama nazwa wskazuje służy do noszenia granatów. Wróć, to nie chlebak :-)

Służy do wybierania. A, że we wtyczkach chcemy często znaleźć informację, np. o filmach, to mechanizm wybierania (wskazywania) co jest dla nas interesujące jest pożądany.


#### Podstawy selekcji

Dla zaprezentowania co selektor wybiera dodam do wskazanych elementów wytłuszczenie (pogrubienie, jakby ktoś nie widział :-))


Weźmy fragment HTML:
```html
<h1>Mój nagłówek</h1>
<div class="box">
  <div>
    <p id="pierwszy">Pierwszy akapit.</p>
    <p>Drugi akapit – <span class="bold">grubo<span> i <i>pochyło</i>.</p>
  </div>
</div>
<p>Ekstra <i>akapit</i>.</p>
<div class="bold">pa</div>
```

##### tag
Chcemy wskazać `h1`, to selektor jest... `h1`. 
Magia nie? Po prostu nazwa znacznika (taga) jest jego selektorem.

> __Mój nagłówek__
> Pierwszy akapit.
> Drugi akapit – grubo i _pochyło_.
> Ekstra _akapit_.
> pa

Selektor znacznika wybiera wszystkie elementy, Czyli dla `p` mamy:

> Mój nagłówek
> __Pierwszy akapit.__
> __Drugi akapit – grubo i _pochyło_.__
> __Ekstra _akapit_.__
> pa

##### id

Możemy zaznaczyć po ID, czyli ten element (powinien być unikalny), którego nazwa jest w atrybucie `id=""`.
Dla selektora `#pierwszy` jak i `p#pierwszy` mamy:

> Mój nagłówek
> __Pierwszy akapit.__
> Drugi akapit – grubo i _pochyło_.
> Ekstra _akapit_.
> pa

Za to `div#pierwszy` nic nie złapie. Nie ma `div` z ID `pierwszy`.

##### class

Można też wskazać po klasie, np. `.bold`:

> Mój nagłówek
> Pierwszy akapit.
> Drugi akapit – __grubo__ i _pochyło_.
> Ekstra _akapit_.
> __pa__

Przy czym `span.bold` złapie tylko „_grubo_” a `div.bold` tylko „_pa_”.
Można łączyć z id, a także użyć więcej klas, np. `p#pierwszy.bold.error` (nic nie złapie, bo szuka `<p>` z id `pierwszy` z klasą `bold` i klasą `error`).

A propos klas, to element może mieć ich wiele, oddzielonych spacjami. Kolejność nie gra roli.

##### i pozostałe

Jest więcej selektorów, np. atrybutów itd. Odsyłam np. do http://www.kurshtml.edu.pl/css/selektory.html


#### Selektory złożone

Selektory złożone to takie, które określają swoje położenie względem siebie, np. potomek, brat.


##### potomek

Potomek, to element jakkolwiek głęboko zawarty w drugim. Np. `div p`:

> Mój nagłówek
> __Pierwszy akapit.__
> __Drugi akapit – grubo i _pochyło_.__
> Ekstra _akapit_.
> pa

Zaznaczył `<p>` ale tylko te, które są w `<div>`. Tak samo będzie dla `div.box p`, mimo, że `<p>` jest wnukiem `<div class="box">`.


##### dziecko

Dziecko to tylko bezpośredni potomek. Czyli `div > p` da wynik jak wyżej, ale `div.box > p` nie ze wskaże (nie ma `<p>` bezpośrednio w `<div class="box">`.


##### brat

Można wskazać element, który jest bezpośrednio poprzedzony innym, np. `p + p`:

> Mój nagłówek
> Pierwszy akapit.
> __Drugi akapit – grubo i _pochyło_.__
> Ekstra _akapit_.
> pa

Powtarzam, bezpośrednio. `h1 + p` nic nam nie da (rozdziela je `<div>`).


##### ogólny brat

Można też poprosić o element jakkolwiek poprzedzony, np. `h1 ~ p` (teraz `<div>` w środku nie ma znaczenia):

> Mój nagłówek
> Pierwszy akapit.
> Drugi akapit – grubo i _pochyło_.
> __Ekstra _akapit_.__
> pa


#### Reszta

Polecam jakiś kurs HTML/CSS, albo bezpośrednio https://www.w3schools.com/cssref/css_selectors.asp czy https://developer.mozilla.org/pl/docs/Learn/CSS/Introduction_to_CSS/Selektory (po polsku).


### Testy
Selektor to bardzo silne narzędzie.
Aby móc przrte

