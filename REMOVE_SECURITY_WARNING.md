# הסרת אזהרת אבטחה של Windows

## הבעיה
כאשר מפעילים את `start_simple.bat`, Windows מציג אזהרת אבטחה "Unknown Publisher" וצריך ללחוץ "Run".

## פתרון 1: הסרה חד-פעמית (מהירה)
1. בחלון האזהרה, סמן את התיבה: ☑ "Always ask before opening this file"
2. לחץ "Run"
3. בפעם הבאה לא תופיע האזהרה

## פתרון 2: הסרה קבועה (מומלץ)
1. לחץ לחיצה ימנית על `start_simple.bat`
2. בחר **Properties** (מאפיינים)
3. בתחתית החלון, ליד "Security:", סמן את התיבה: ☑ **Unblock**
4. לחץ **OK**
5. מעכשיו הקובץ יפעל ללא אזהרה

## פתרון 3: שינוי הגדרות Windows (מתקדם)
### דרך A: Group Policy
1. לחץ `Win + R`
2. הקלד: `gpedit.msc` ולחץ Enter
3. נווט אל: **User Configuration** > **Administrative Templates** > **Windows Components** > **Attachment Manager**
4. פתח את **"Inclusion list for low file types"**
5. סמן **Enabled**
6. בתיבת טקסט, הקלד: `.bat`
7. לחץ **OK**

### דרך B: Registry (זהירות!)
1. לחץ `Win + R`
2. הקלד: `regedit` ולחץ Enter
3. נווט אל: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Policies\Associations`
4. צור/ערוך את הערך `LowRiskFileTypes` (סוג: String)
5. הוסף `.bat` לרשימה
6. סגור את Registry Editor
7. הפעל מחדש את המחשב

---

## למה זה קורה?
Windows מגן עליך מפני קבצים שהורדו מהאינטרנט או שנוצרו על ידי תוכנות לא מוכרות. 
הקובץ `start_simple.bat` הוא קובץ Batch רגיל ובטוח לחלוטין, אבל Windows לא יכול לדעת את זה.

---

**המלצה:** השתמש בפתרון 2 (Unblock) - זה הכי פשוט ובטוח.
