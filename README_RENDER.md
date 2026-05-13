# 🏗️ نظام متابعة مشاريع البناء والاستثمار
## Construction & Investment Project Tracker

---

## 🚀 النشر على Render.com (مجاني)

### الخطوة 1: إنشاء حساب
1. ادخل على [render.com](https://render.com)
2. سجل حساب جديد (مجاني)
3. اربط حسابك بـ GitHub

### الخطوة 2: رفع الملفات على GitHub

#### أ. أنشئ repository جديد
```
اسم المستودع: construction-tracker
```

#### ب. ارفع الملفات دي:
```
📁 construction-tracker/
   ├── server.py          ✅ (السيرفر)
   ├── index.html         ✅ (الواجهة)
   ├── requirements.txt   ✅ (المكتبات)
   ├── render.yaml        ✅ (إعدادات Render)
   └── Procfile           ✅ (أوامر التشغيل)
```

#### ج. أو استخدم Git مباشرة:
```bash
# 1. نزل الملفات من الرابط
# 2. افتح Terminal في المجلد
cd construction-tracker

# 3. inicialize git
git init
git add .
git commit -m "Initial commit"

# 4. اربط بالـ GitHub
git remote add origin https://github.com/YOUR_USERNAME/construction-tracker.git
git branch -M main
git push -u origin main
```

### الخطوة 3: النشر على Render.com

1. في Render Dashboard، اضغط **"New +"**
2. اختار **"Web Service"**
3. اربط مستودع GitHub
4. املأ الإعدادات:

| الإعداد | القيمة |
|---------|--------|
| **Name** | construction-tracker |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn server:app --bind 0.0.0.0:$PORT` |
| **Plan** | Free |

5. اضغط **"Create Web Service"**
6. انتظر 2-3 دقائق للـ Build
7. افتح الرابط: `https://construction-tracker.onrender.com`

---

## 📦 الملفات المرفقة

| الملف | الوظيفة |
|-------|---------|
| `server.py` | السيرفر (Flask + SQLite) |
| `index.html` | الواجهة الأمامية |
| `requirements.txt` | مكتبات Python المطلوبة |
| `render.yaml` | إعدادات Render.com |
| `Procfile` | أمر التشغيل |

---

## 🔧 للتشغيل المحلي (على جهازك)

```bash
# 1. نزل المكتبات
pip install -r requirements.txt

# 2. شغل السيرفر
python server.py

# 3. افتح المتصفح
# http://localhost:5000
```

---

## 💾 قاعدة البيانات

- **المحلي**: ملف `construction.db` في نفس المجلد
- **أونلاين**: Render.com بيحفظ الملف في الـ disk (يفضل تفعيل Disk)

### لتفعيل Disk على Render.com:
1. في Dashboard → Settings
2. اضغط **"Disks"**
3. اضف Disk جديد:
   - **Name**: construction-db
   - **Mount Path**: `/var/www/construction`
   - **Size**: 1 GB (كافي جداً)

---

## 🌟 المميزات

- ✅ قاعدة بيانات SQLite (البيانات متضيعش)
- ✅ إضافة/تعديل/حذف المشاريع والمقاولين
- ✅ تسجيل الدفعات مع الاحتفاظ (Retainage)
- ✅ تقارير مالية ورسوم بيانية
- ✅ تصدير واستيراد البيانات
- ✅ يشتغل 24/7 على Render.com
- ✅ مجاني تماماً!

---

## 📞 للدعم

لو واجهت أي مشكلة، قوللي!
