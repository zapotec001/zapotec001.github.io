# Tarihte Bugün
Minimal ve şık tasarımlı bu web sayfası, Wikipedia'nın Türkçe "Tarihte Bugün" arşivinden çektiği içerikleri Türkçe olarak sunar. Her olay kartı, ilgili maddelere düzgün bağlantılar ve varsa öne çıkan görsellerle birlikte gelir.

## Özellikler
- Türkçe Wikipedia On This Day API'sinden günlük olayların otomatik olarak alınması
- Olay kartlarında bağlantıların temiz bir şekilde gösterilmesi
- İlgili maddelerden bulunan yüksek çözünürlüklü görsellerin (varsa) olay kartlarında yer alması
- Minimal cam efektli tema ve mobil uyumlu düzen

## Geliştirme
Yerelde hızlıca incelemek için herhangi bir statik sunucu yeterlidir:

```bash
python -m http.server 8000
```

Ardından tarayıcınızda [`http://127.0.0.1:8000`](http://127.0.0.1:8000) adresini açın.

Flask sürümünü çalıştırmak için:

```bash
pip install flask
flask --app app.py run
```
