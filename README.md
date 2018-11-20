pdom – DOM parser
=================

Simple DOM regex parser. Faster and more powerful version of ParseDOM() with selectors.

Just parsing HTML/XML pages. Faster then BeautySoap, much slower then lxml but is writen in pure Python.
Useful in [Kodi](https://kodi.tv) addons. It replaces old [ParseDOM](https://kodi.wiki/view/Add-on:Parsedom_for_xbmc_plugins) function.


## First look

Get links and build Kodi folder.

```python
url = 'http://animezone.pl'
r = client.request(urljoin(url, '/anime/lista'))
for a in pdom.select(r, 'div.anime-list div a'):
    addon.addDir(a.text, urljoin(url, a.href), mode=3)
```

To see nested elements (`href` from `a` nested `img.src`).

```href
<a href="watch.php?id=15">
  <img src="ch_logo/elevensports1.png">
</a>
```

```bash
python3 -m dom  http://wizja.tv 'a[href*=watch](href) img(src)'
```

```python
url = 'http://wizja.tv'
with requests.Session() as sess:
    for (link,), (logo,) in dom.select(sess.get(url), 'a[href*=watch](href) img(src)'):
        print('url={link!r}, logo={logo!r}.format(link=link, logo=logo))
```


More documentation in [English](./doc/en/dom.md) and [Polish](./doc/pl/dom.md).

