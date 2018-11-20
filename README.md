pdom – DOM parser
=================

Simple DOM regex parser. Faster and more powerful version of ParseDOM() with selectors.

Just parsing HTML/XML pages. Faster then BeautySoap, much slower then lxml but is writen in pure Python.
Useful in [Kodi](https://kodi.tv) addons. It replaces old [ParseDOM](https://kodi.wiki/view/Add-on:Parsedom_for_xbmc_plugins) function.


## First look

To see links try:

```bash
python3 -m dom  http://wizja.tv 'a[href*=watch](href) img(src)'
```

From python:

```python
url = 'http://wizja.tv'
with requests.Session() as sess:
    for a, logo in dom.select(sess.get(url), 'a[href*=watch] img'):
        print('url={a.href}, logo={logo.src}.format(**locals()))
```


More documentation in [English](./doc/en/dom.md) and [Polish](./doc/pl/dom.md).

