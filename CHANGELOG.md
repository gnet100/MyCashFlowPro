# 📋 יומן שינויים - Changelog

## M4-P3-BANKIN-PARSER - הוספת Parser לBankin DAT (08/11/2025)

### ⭐ Parser חדש לקבצי DAT (Bankin)

---

### ✨ Parser חדש

#### Bankin DAT Parser
- **קובץ:** `parsers/bankin_dat_parser.py` (250 שורות)
- **תמיכה:** קבצי DAT ממערכת Bankin (קידוד DOS cp862)
- **זיהוי:** קבצים עם "bankin" בשם + סיומת .dat
- **יכולות:**
  - תמיכה מלאה בקידוד cp862 (DOS Hebrew)
  - תיקון אוטומטי של טקסט עברי הפוך
  - המרת תאריכים DDMMYY → datetime
  - חישוב סיכומים (זכות, חובה, יתרות)
  - 40 עסקאות בקובץ דוגמה
- **פורמט:** מספר,תאריך,תיאור,סכום,יתרה,קוד,חשבון

---

### 🔧 עדכונים

#### file_service.py
- **שורה 20:** הוספת import של BankinDATParser
- **שורות 415-440:** לוגיקת זיהוי DAT מורחבת:
  - זיהוי אוטומטי של Bankin לפי שם קובץ
  - תמיכה גם ב-Leumi DAT
  - ברירת מחדל ל-Bankin

#### parsers/__init__.py
- **חדש:** הוספת ייצוא של BankinDATParser

---

## M4-P2-PARSERS-EXTENDED - הרחבת תמיכה בפורמטים (08/11/2025)

### ⭐ הרחבת תמיכה בפורמטים + תיקוני באגים

---

### ✨ Parsers חדשים (2)

#### 1. Leumi PDF Parser
- **קובץ:** `parsers/leumi_pdf_parser.py` (180 שורות)
- **תמיכה:** תנועות בחשבון לאומי PDF
- **זיהוי:** קבצים עם "לאומי" או "תנועות" בשם + סיומת .pdf
- **טכנולוגיה:** PyPDF2 לחילוץ טקסט
- **הערה:** פורמט PDF מהבנק לעיתים פגום, מומלץ XLSX

#### 2. Leumi XLSX Parser ⭐
- **קובץ:** `parsers/leumi_xlsx_parser.py` (165 שורות)
- **תמיכה:** תנועות בחשבון לאומי XLSX
- **זיהוי:** קבצים עם "עו_ש", "תנועות" או "לאומי" בשם + .xlsx
- **יכולות:**
  - זיהוי אוטומטי של שורת כותרת
  - חילוץ מספר חשבון
  - 42 עסקאות בקובץ דוגמה
  - תמיכה בהכנסות והוצאות

---

### 🔧 תיקוני באגים (5)

#### Bug #1: שדות DB חסרים
**הבעיה:** `table transactions has no column named date`  
**הפתרון:** שינוי ל-`transaction_date`, הוספת `transaction_type` ו-`source_type`

#### Bug #2: חבילות חסרות
**הבעיה:** html5lib, beautifulsoup4 לא מותקנים  
**הפתרון:** נוספו ל-requirements.txt + הנחיות התקנה

#### Bug #3: קבצי XLS ישנים
**הבעיה:** קבצי .xls לא נקראים  
**הפתרון:** שימוש מפורש ב-`engine='xlrd'`

#### Bug #4: HTML frameset לא נתמך
**הבעיה:** קבצי XLS מהבנק הם HTML עם קבצים חיצוניים  
**הפתרון:** הנחיה למשתמש להמיר ל-XLSX דרך Excel

#### Bug #5: כפתור עיבוד נעלם
**הבעיה:** כפתור "עיבוד נתוני קובץ" נעלם אחרי עיבוד  
**הפתרון:** כפתור נשאר תמיד, מושבת + דהוי (opacity 0.4) אם עובד

---

### 📦 חבילות חדשות

```
html5lib==1.1           # HTML parsing
beautifulsoup4==4.12.2  # HTML parsing
PyPDF2==3.0.1          # PDF parsing
```

---

### 🎨 שינויי UI

#### CSS:
```css
.filter-btn-success:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}
```

#### HTML:
```html
<button 
    class="filter-btn filter-btn-success" 
    {% if file.processed %}disabled{% endif %}
    style="{% if file.processed %}opacity: 0.4;{% endif %}">
    עיבוד נתוני קובץ
</button>
```

---

### 📊 סטטיסטיקות

**Parsers:**
- דיסקונט: 59 עסקאות ✅
- ויזה כאל: 2 עסקאות ✅
- לאומי PDF: תמיכה מוגבלת
- לאומי XLSX: 42 עסקאות ✅

**קוד חדש:**
- 2 parsers: ~345 שורות
- תיקוני file_service: ~50 שורות
- שיפורי UI: ~30 שורות

**זמן פיתוח:** ~4 שעות

---

## M4-P2-COMPLETE - Milestone 4 Part 2 - עיבוד קבצים אוטומטי (08/11/2025)

### ⭐ מערכת עיבוד אוטומטי מלאה לקבצי בנקים

---

### ✨ תכונות חדשות

#### 1. Parser לויזה כאל (בנק לאומי)
- ✅ **קריאת קבצי Excel** של כרטיס ויזה כאל
- ✅ **דילוג אוטומטי** על 3 שורות כותרת
- ✅ **המרת תאריכים וסכומים** אוטומטית
- ✅ **חילוץ 4 ספרות אחרונות** של הכרטיס
- ✅ **זיהוי ענפים** - הצעת קטגוריה מהבנק
- ✅ **הסרת שורות סיכום** אוטומטית

**קובץ:** `parsers/visa_cal_parser.py` (170 שורות)

#### 2. מערכת עיבוד מרכזית
- ✅ **זיהוי אוטומטי חכם** - 3 שכבות זיהוי:
  1. לפי שם מקורי של הקובץ
  2. לפי מילות מפתח (דיסקונט, ויזה, לאומי)
  3. לפי תוכן הקובץ (עמודות)
- ✅ **עיבוד לעסקאות** - המרה אוטומטית לטבלת transactions
- ✅ **מניעת עיבוד כפול** - בדיקת סטטוס processed
- ✅ **הודעות שגיאה מפורטות** - כולל רשימת עמודות בקובץ

**קובץ:** `services/file_service.py` - פונקציה `process_file_to_transactions()`

#### 3. API Endpoint חדש
- ✅ **POST /files/<id>/process** - עיבוד קובץ לעסקאות
- ✅ **Response עם מספר עסקאות** שנוצרו
- ✅ **טיפול מלא בשגיאות**

**קובץ:** `routes/files.py`

#### 4. ממשק משתמש משופר
- ✅ **כפתור "עיבוד נתוני קובץ"** בטבלת קבצים
- ✅ **הצגה רק לקבצים שלא עובדו**
- ✅ **הסרת דיאלוג אישור** - עיבוד ישיר
- ✅ **הודעות משוב** - "מעבד קובץ..." ו-"נוצרו X עסקאות"
- ✅ **רענון אוטומטי** לאחר עיבוד מוצלח

**קובץ:** `templates/files/files.html`

---

### 🔧 תיקוני באגים

#### Bug #1: זיהוי קבצים כושל
**הבעיה:** המערכת בדקה את שם ה-hash במקום השם המקורי  
**הפתרון:** שליפת `original_filename` מהמסד + 3 שכבות זיהוי

#### Bug #2: Parser כללי לא תומך
**הבעיה:** fallback ל-FileParser שאינו מעבד עסקאות  
**הפתרון:** זיהוי אוטומטי לפי תוכן הקובץ עם ניסיון דיסקונט וויזה

#### Bug #3: דיאלוג מיותר
**הבעיה:** דיאלוג "האם לעבד..." אחרי לחיצה על כפתור  
**הפתרון:** הסרת `confirm()` - עיבוד ישיר

---

### 📊 נתונים מעובדים

**קובץ דיסקונט:**
- 📁 `transaction-details_export_1762616024732.xlsx`
- ✅ 59 עסקאות מוכנות לעיבוד
- ⏱️ טווח: 23/07/2025 - 30/10/2025
- 💳 זיהוי תשלומים: תשלום X מתוך Y

**קובץ ויזה כאל:**
- 📁 `פירוט_חיובים_לכרטיס_ויזה_1234-_08_11_25.xlsx`
- ✅ 2 עסקאות מוכנות לעיבוד
- ⏱️ טווח: 27/10/2025 - 04/11/2025
- 🏪 זיהוי ענף: "מזון ומשקאות"

---

### 🗂️ קבצים חדשים/משונים

#### קבצים חדשים:
```
parsers/
  └── visa_cal_parser.py         170 שורות ⭐ חדש!
```

#### קבצים ששונו:
```
services/
  └── file_service.py            +115 שורות (process_file_to_transactions)

routes/
  └── files.py                   +47 שורות (POST endpoint)

templates/files/
  └── files.html                 +60 שורות (כפתור + JS + CSS)
```

---

### 🎨 שינויים בעיצוב

#### CSS חדש:
```css
.filter-btn-success {
    background: #28A745;
    color: var(--white);
}

.filter-btn-success:hover {
    background: #218838;
}
```

#### JavaScript חדש:
```javascript
async function processFile(fileId, filename) {
    showMessage('מעבד קובץ...', 'info');
    
    const response = await fetch(`/files/${fileId}/process`, {
        method: 'POST'
    });
    
    if (data.success) {
        showMessage(`נוצרו ${data.num_transactions} עסקאות`, 'success');
        setTimeout(() => window.location.reload(), 1500);
    }
}
```

---

### 📱 זרימת עבודה מלאה

```
1. העלאת קובץ
   ↓
2. שמירה ב-data/files/
   ↓
3. רישום בטבלת files (processed=0)
   ↓
4. לחיצה על "עיבוד נתוני קובץ"
   ↓
5. זיהוי אוטומטי (שם → תוכן → fallback)
   ↓
6. הרצת parser מתאים (דיסקונט/ויזה)
   ↓
7. המרה ל-transactions
   ↓
8. INSERT לטבלת transactions (category_id=0)
   ↓
9. UPDATE files (processed=1, num_transactions=X)
   ↓
10. ✅ הצלחה! הצגת הודעה
```

---

### 📊 סטטיסטיקות

- **קבצים חדשים:** 1 (visa_cal_parser.py)
- **קבצים ששונו:** 3
- **שורות קוד חדשות:** ~222
- **API endpoints:** +1 (סה"כ 8)
- **Parsers פעילים:** 2 (דיסקונט, ויזה כאל)
- **זמן פיתוח:** ~2 שעות
- **עסקאות מוכנות:** 61 (59 + 2)

---

## M3-P1-ALL-FIXES - Milestone 3 Part 1 + 6 תיקונים (03/11/2025)

### ⭐ הגרסה המלאה והסופית של Milestone 3 חלק 1

---

### ✨ תכונות חדשות - דף ניהול קטגוריות

#### 1. עץ קטגוריות היררכי
- ✅ **3 רמות** עם צבעים שונים:
  - 🟣 רמה 1: gradient סגול-כחול
  - 🌸 רמה 2: gradient ורוד-אדום
  - 🔵 רמה 3: gradient כחול-תכלת
- ✅ **הזחה חזותית** ברורה:
  - רמה 2: 3rem + קו בצד
  - רמה 3: 6rem + קו בצד
- ✅ **הרחבה/כיווץ** של ענפים:
  - לחיצה על ▶ פותח/סוגר ענף
  - כפתור "📂 הרחב הכל"
  - כפתור "📁 כווץ הכל"
  - מתחיל במצב **מכווץ**

#### 2. CRUD מלא לקטגוריות
- ✅ **הוספה** (➕ הוסף קטגוריה חדשה)
  - מודל צף יפה
  - שדה שם (חובה)
  - בחירת קטגוריית אב (אופציונלי)
  - dropdown עם הזחות ויזואליות
  - הסבר: "בחר קטגוריית אב אם זו תת-קטגוריה"
  
- ✅ **עריכה** (✏️ ערוך)
  - פתיחת מודל עם נתונים קיימים
  - שינוי שם
  - עדכון נתיב מלא אוטומטי
  
- ✅ **מחיקה** (🗑️ מחק)
  - אישור מחיקה
  - בדיקות אבטחה:
    - לא ניתן למחוק עם תתי-קטגוריות
    - לא ניתן למחוק עם רשומות
    - לא ניתן למחוק קטגוריות מערכת
  - הודעת שגיאה ברורה אם לא ניתן

#### 3. סטטיסטיקות קטגוריות
- ✅ **4 כרטיסים צבעוניים:**
  1. סגול: סה"כ קטגוריות
  2. ירוק: קטגוריות בשימוש
  3. כתום: רשומות לא מסווגות + הסבר
  4. כחול: קטגוריות ראשיות

#### 4. מונה רשומות
- ✅ כל קטגוריה מציגה **מספר רשומות**
- ✅ עדכון אוטומטי עם המערכת

---

### 🔧 6 תיקונים חשובים

#### תיקון #1: כפתורי הרחבה/כיווץ עובדים
**הבעיה:** הכפתורים לא עשו כלום  
**הפתרון:**
```javascript
// העץ מתחיל במצב collapsed
<div class="tree-children collapsed" id="children-{{ category.id }}">

// כפתורי הרחבה/כיווץ עובדים על ה-collapsed class
function expandAll() {
  document.querySelectorAll('.tree-children').forEach(el => {
    el.classList.remove('collapsed');
  });
}
```

#### תיקון #2: בחירת קטגוריית אב עובדת
**הבעיה:** לא ניתן היה לבחור קטגוריית אב  
**הפתרון:**
```html
<!-- Dropdown משופר -->
<select id="parentCategory" style="min-height: 40px;">
  <option value="">--- אין - קטגוריה ראשית ---</option>
  {% for cat in categories %}
    {% if cat.level < 3 %}
    <option value="{{ cat.id }}">{{ '  ' * (cat.level - 1) }}{{ cat.name }}</option>
    {% endif %}
  {% endfor %}
</select>
<small>בחר קטגוריית אב אם זו תת-קטגוריה</small>
```

#### תיקון #3: אייקון רשומות חדש
**הבעיה:** האייקון 🗄️ לא התאים  
**הפתרון:**
```html
<!-- base.html -->
<li><a href="/transactions">
  <span class="nav-icon">💾</span> רשומות  <!-- שונה מ-🗄️ -->
</a></li>
```

#### תיקון #4: הסבר "לא מסווגות"
**הבעיה:** לא ברור מה זה "לא מסווגות"  
**הפתרון:**
```html
<div class="cat-stat-card orange">
  <div class="cat-stat-number">2</div>
  <div class="cat-stat-label">רשומות לא מסווגות</div>
  <div style="font-size: 0.75rem;">רשומות ללא קטגוריה</div>
</div>
```
**משמעות:** רשומות עם `category_id = 0` או `NULL`

#### תיקון #5: הסרת הודעות alert
**הבעיה:** הודעות alert מעצבנות אחרי כל פעולה  
**הפתרון:**
```javascript
// לפני:
if (data.success) {
  alert(data.message);  // ❌ מעצבן!
  window.location.reload();
}

// אחרי:
if (data.success) {
  // ✅ פשוט טוען מחדש בשקט
  closeModal();
  window.location.reload();
}
```
**שגיאות עדיין מוצגות!** רק הצלחות מסתרות.

#### תיקון #6: הזחה ברורה
**הבעיה:** קשה לראות מי תת-קטגוריה של מי  
**הפתרון:**
```css
.tree-item.level-2 {
  margin-right: 3rem;  /* היה: 2rem */
  padding-right: 1rem;
  border-right: 3px solid rgba(255,255,255,0.3);  /* חדש! */
}

.tree-item.level-3 {
  margin-right: 6rem;  /* היה: 4rem */
  padding-right: 1rem;
  border-right: 3px solid rgba(255,255,255,0.3);  /* חדש! */
}
```

---

### 📋 API Endpoints חדשים

#### `/categories` - דף הניהול
```python
@categories_bp.route('/')
def manage():
    categories = get_category_tree()
    tree = build_hierarchical_tree(categories)
    stats = get_category_stats()
    return render_template('categories/manage.html', ...)
```

#### `/categories/api/list` - רשימה
```python
@categories_bp.route('/api/list', methods=['GET'])
def api_list():
    categories = get_category_tree()
    return jsonify({'success': True, 'categories': categories})
```

#### `/categories/api/tree` - עץ
```python
@categories_bp.route('/api/tree', methods=['GET'])
def api_tree():
    tree = build_hierarchical_tree(get_category_tree())
    return jsonify({'success': True, 'tree': tree})
```

#### `/categories/api/get/<id>` - פרטים
```python
@categories_bp.route('/api/get/<int:category_id>', methods=['GET'])
def api_get(category_id):
    # מחזיר פרטי קטגוריה + מונה רשומות + מונה ילדים
```

#### `/categories/api/add` - הוספה
```python
@categories_bp.route('/api/add', methods=['POST'])
def api_add():
    # מקבל: name, parent_id
    # מחשב: level, full_path
    # בודק: מקסימום 3 רמות
```

#### `/categories/api/update/<id>` - עדכון
```python
@categories_bp.route('/api/update/<int:category_id>', methods=['PUT'])
def api_update(category_id):
    # מעדכן: name, full_path
    # מעדכן רקורסיבית את כל הילדים
```

#### `/categories/api/delete/<id>` - מחיקה
```python
@categories_bp.route('/api/delete/<int:category_id>', methods=['DELETE'])
def api_delete(category_id):
    # בודק: לא מערכת, אין ילדים, אין רשומות
```

---

### 🗂️ קבצים חדשים/משונים

#### קבצים חדשים:
```
routes/
  └── categories.py          474 שורות, Blueprint מלא

templates/
  └── categories/
      └── manage.html        550 שורות, דף מלא עם CSS + JS

README.md                    עודכן למצב M3-P1
CHANGELOG.md                 הקובץ הזה
PROJECT-STATUS.md            חדש! מצב פרויקט מפורט
NEXT-SESSION-GUIDE.md        חדש! הנחיות לשיחה הבאה
```

#### קבצים ששונו:
```
app.py                       +2 שורות (רישום categories_bp)
templates/base.html          שורה 34: שינוי אייקון רשומות
```

---

### 🎨 שינויים בעיצוב

#### CSS Classes חדשות בdaf קטגוריות:
```css
/* עץ */
.category-tree, .tree-item, .tree-item-header
.tree-item-name, .tree-item-stats, .tree-item-count
.tree-item-actions, .tree-children, .expand-icon

/* צבעים לפי רמות */
.tree-item.level-1, .tree-item.level-2, .tree-item.level-3

/* סטטיסטיקות */
.cat-stats-grid, .cat-stat-card
.cat-stat-card.green, .cat-stat-card.orange, .cat-stat-card.blue
.cat-stat-number, .cat-stat-label

/* טפסים */
.form-group, .form-actions

/* מודל */
.modal, .modal.active, .modal-content
.modal-header, .modal-close
```

#### אנימציות:
```css
/* hover על פריט בעץ */
.tree-item:hover {
  background: var(--medium-gray);
  transform: translateX(-3px);
}

/* סיבוב חץ בהרחבה */
.expand-icon.expanded {
  transform: rotate(90deg);
}

/* טרנזישנים */
transition: all 0.3s;
```

---

### 🐛 תיקוני באגים נוספים

#### 1. מאקרו Jinja2
**בעיה:** `render_tree_item` לא מוגדר  
**תיקון:** העברת המאקרו לתחילת הקובץ (לפני השימוש)

#### 2. עדכון רקורסיבי
**בעיה:** שינוי שם קטגוריה לא עדכן את הילדים  
**תיקון:**
```python
def update_children_paths(cursor, category_id):
    # עדכון רקורסיבי של full_path לכל הילדים
    # מחשב מחדש level
```

#### 3. מניעת מחיקה מסוכנת
**בעיה:** ניתן היה למחוק קטגוריה עם נתונים  
**תיקון:**
```python
# בדיקת ילדים
cursor.execute('SELECT COUNT(*) FROM categories WHERE parent_id = ?')
# בדיקת רשומות
cursor.execute('SELECT COUNT(*) FROM transactions WHERE category_id = ?')
# בדיקת מערכת
if is_system: return error
```

---

### 📱 Responsive Design

הכל עובד גם במסכים קטנים:
```css
@media (max-width: 768px) {
  .cat-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .tree-item.level-2 {
    margin-right: 1.5rem;
  }
  
  .tree-item.level-3 {
    margin-right: 3rem;
  }
}
```

---

### 🔄 תהליך פיתוח השיחה

#### שלב 1: Blueprint + API (30 דק')
- יצירת `routes/categories.py`
- כל ה-CRUD endpoints
- לוגיקת עץ היררכי

#### שלב 2: Template (45 דק')
- יצירת `templates/categories/manage.html`
- עץ עם מאקרו רקורסיבי
- CSS מלא
- JavaScript לאינטראקטיביות

#### שלב 3: תיקון באגים (1 שעה)
- תיקון מאקרו Jinja2
- 6 תיקונים לפי פידבק משתמש
- בדיקות

---

### 📊 סטטיסטיקות

- **קבצים חדשים:** 4 (categories.py, manage.html, PROJECT-STATUS.md, NEXT-SESSION-GUIDE.md)
- **קבצים ששונו:** 4 (app.py, base.html, README.md, CHANGELOG.md)
- **שורות קוד חדשות:** ~1200
- **API endpoints:** 7
- **CSS classes חדשות:** ~30
- **זמן פיתוח:** ~3 שעות
- **תיקונים:** 6 (כולם עובדים!)

---

## גרסה 1.3 - שדרוג UI (03/11/2025)

### ✨ תכונות
- ✅ תפריט עליון עם אייקונים
- ✅ כרטיסי סטטיסטיקה בדף הבית
- ✅ מערכת תזרימים

---

## גרסה 1.2 - דף טבלאות (03/11/2025)

### ✨ תכונות
- ✅ דף טבלאות DB מפורט
- ✅ הצגת מבנה ונתונים
- ✅ מפת קשרים

---

## גרסה 1.1 - Milestone 2 (02/11/2025)

### ✨ תכונות
- ✅ נתוני Mock Data
- ✅ דף רשומות

---

## גרסה 1.0 - Milestone 1 (01/11/2025)

### ✨ תכונות
- ✅ תשתית בסיסית
- ✅ 14 טבלאות
- ✅ Flask server

---

## 🎯 מה הלאה?

### Milestone 3 - חלק 2 (מתוכנן)
- ⏳ עדכון קטגוריה מרשומות
- ⏳ מיפוי קטגוריות בנק
- ⏳ כללי למידה

### Milestone 4 (מתוכנן)
- ⏳ למידה אוטומטית
- ⏳ AI לסיווג

### Milestone 5 (מתוכנן)
- ⏳ דוחות וגרפים
- ⏳ ייצוא נתונים

---

**עודכן:** 03/11/2025 17:00  
**גרסה נוכחית:** M3-P1-ALL-FIXES  
**Milestone:** 3 חלק 1 (מושלם!)  
**קבצים חדשים:** 4  
**שורות קוד:** ~1200
