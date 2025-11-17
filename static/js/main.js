// main.js
// JavaScript בסיסי לאפליקציה

console.log('🚀 מערכת ניהול כספים - Milestone 1');

// פונקציות עזר כלליות
const Utils = {
    // פורמט מספרים עם פסיקים
    formatNumber: function(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },
    
    // פורמט תאריך
    formatDate: function(dateString) {
        const date = new Date(dateString);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    },
    
    // הצגת הודעה
    showMessage: function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        
        // הוסף בתחילת הדף
        const main = document.querySelector('main');
        if (main) {
            main.insertBefore(alertDiv, main.firstChild);
            
            // הסר אחרי 5 שניות
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }
};

// אירועים כשהדף נטען
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ הדף נטען בהצלחה');
    
    // הוסף אנימציה לכרטיסי סטטיסטיקה
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.5s ease';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 50);
        }, index * 100);
    });
});
