# Tarihte Bugün – Yönetilebilir Tarih Akışı

Bu proje, Wikipedia'nın Türkçe “Tarihte Bugün” beslemesinden aldığı içerikleri cam etkili bir arayüzle sergileyen ve aynı zamanda yönetici paneli üzerinden tamamen kontrol edilebilir hale getiren bir Flask uygulamasıdır. İster otomatik olarak gelen olayları kullanın ister kendi haberlerinizi ekleyin; tüm bağlantılar temizlenir, görseller desteklenir ve düzenlemeler kolayca yapılır.

## Öne Çıkan Özellikler
- 🎯 **Dinamik içerik deposu:** Türkçe “On This Day” API’sinden çekilen olaylar JSON dosyasında saklanır; yönetici panelinden düzenlenebilir veya elle eklenebilir.
- 🖼️ **Zengin kart tasarımları:** Her kart kategori rozetleri, yıl bilgisi, görsel (varsa) ve temiz bağlantılarla cam efekti tema üzerinde sunulur.
- 🛠️ **Yönetim paneli:** /admin üzerinden giriş yaparak içerikleri listeleyebilir, düzenleyebilir, silebilir veya tek tuşla bugünün olaylarını yeniden çekebilirsiniz.
- 🔒 **Basit erişim kontrolü:** Ortam değişkenleriyle kullanıcı adı ve şifreyi belirleyin; oturum açanlar için ek navigasyon öğeleri otomatik görünür.
- ⚡ **Hızlı deneyim:** Uzun metinler filtrelenir, görsel bağlantıları normalize edilir ve ön uçta hafif animasyonlarla kullanıcı deneyimi güçlendirilir.

## Kurulum
1. Gerekli bağımlılıkları yükleyin:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows için .venv\Scripts\activate
   pip install flask
   ```
2. Ortam değişkenlerini ayarlayın (isteğe bağlı):
   ```bash
   export FLASK_APP=app.py
   export ADMIN_USERNAME=admin        # Varsayılan: admin
   export ADMIN_PASSWORD=admin123     # Varsayılan: admin123
   export SECRET_KEY=bir-super-sir    # Varsayılan: dev-secret-key
   ```
3. Uygulamayı çalıştırın:
   ```bash
   flask run
   ```
   Ardından tarayıcınızdan [http://127.0.0.1:5000](http://127.0.0.1:5000) adresini açın.

## Yönetim Paneli
- `/admin/login` adresinden belirlediğiniz kullanıcı adı ve şifre ile giriş yapın.
- **Bugünün Olaylarını Yenile:** Wikipedia'dan en fazla sekiz olay çekilerek var olan listeyi günceller.
- **Yeni içerik ekle:** Başlık, özet, yıl, kategori, görsel ve kaynak bağlantılarını içeren kartlar oluşturabilirsiniz.
- **Düzenle / Sil:** Var olan kartları güncelleyin veya kalıcı olarak kaldırın. Silme işlemleri için tarayıcı onayı alınır.

Tüm içerikler `data/events.json` dosyasında `last_refreshed` meta bilgisiyle birlikte saklanır; elle düzenlemeniz gerekiyorsa formatı koruduğunuzdan emin olun.

## Statik Ön İzleme
Depo kökündeki `index.html`, cam efekti temanın statik bir örneğini sunar ve GitHub Pages üzerinde bilgi amaçlı yayınlanabilir. Dinamik deneyim için Flask uygulamasını çalıştırmanız gerekir.

## Geliştirme İpuçları
- Yeni stiller eklerken `static/style.css` dosyasındaki değişkenleri kullanarak temayla uyum sağlayın.
- JavaScript tarafında hafif animasyonlar ve formlarda silme onayı için `static/script.js` dosyasını güncelleyin.
- Test amaçlı olarak `python -m compileall app.py` komutu ile sentaks kontrolü yapabilirsiniz.

Katkılarınız ve geri bildirimleriniz için teşekkürler! 📬
