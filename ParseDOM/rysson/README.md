
New DOM support
===============

Simply parsing HTML/XML pages. 

Try:

```bash
python3 -m dom  http://wizja.tv 'a[href*=watch](href) img(src)'
```

From python:

```python
url = 'http://wizja.tv'
with requests.Session() as sess:
    for (link,), (logo,) in dom.select(sess.get(url), 'a[href*=watch](href) img(src)'):
        print(link, logo)
```


More documentation in [English](./doc/en/dom.md) and [Polish](./doc/pl/dom.md).
