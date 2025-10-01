# Tarihte Bugün

Minimal ve şık tasarımlı bu web sayfası, Wikipedia'nın Türkçe "Tarihte Bugün" arşivinden çektiği içerikleri tamamen statik şekilde sunar. Her olay kartı, ilgili maddelere düzgün bağlantılar ve varsa öne çıkan görsellerle birlikte gelir.

## Özellikler
- Türkçe Wikipedia "On This Day" API'sinden (events, births, deaths, holidays, observances) günlük verilerin çekilmesi
- Uzun metinler filtrelenerek kısa ve anlaşılır kartların gösterilmesi
- Olay kartlarında bağlantıların HTML etiketleri olmadan temiz bir şekilde sunulması
- İlgili maddelerden bulunan görsellerin (varsa) olay kartlarında yer alması
- Minimal cam efektli tema, kategori rozetleri ve mobil uyumlu düzen
- Tek tıkla yenileme düğmesi ile verilerin manuel olarak güncellenebilmesi

## Geliştirme
Proje saf HTML/CSS/JS'ten oluştuğu için yerelde hızlıca incelemek üzere herhangi bir statik sunucu yeterlidir:

```bash
python -m http.server 8000
```

Ardından tarayıcınızda [`http://127.0.0.1:8000`](http://127.0.0.1:8000) adresini açın.

### GitHub Pages'e yayınlama
1. Bu depoyu GitHub'da `main` dalına gönderin (push).
2. Depo ayarlarından (Settings → Pages) kaynak olarak `main` ve `/` kök klasörünü seçin.
3. Dakikalar içinde site `https://<kullanici-adiniz>.github.io/` adresinden erişilebilir olur.

İsteğe bağlı olarak `app.py` dosyası aynı verileri Flask ile servis ederek dinamik geliştirme senaryolarında kullanılabilir.
