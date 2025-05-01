// 表单验证
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});

// 表格排序
document.addEventListener('DOMContentLoaded', function() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const index = Array.from(header.parentElement.children).indexOf(header);
                const rows = Array.from(table.querySelectorAll('tbody tr'));
                
                rows.sort((a, b) => {
                    const aValue = a.children[index].textContent;
                    const bValue = b.children[index].textContent;
                    
                    if (header.classList.contains('asc')) {
                        return aValue.localeCompare(bValue);
                    } else {
                        return bValue.localeCompare(aValue);
                    }
                });
                
                const tbody = table.querySelector('tbody');
                rows.forEach(row => tbody.appendChild(row));
                
                headers.forEach(h => h.classList.remove('asc', 'desc'));
                header.classList.toggle('asc');
            });
        });
    });
});

// 数据导出
function exportData(format) {
    const table = document.querySelector('table');
    const rows = Array.from(table.querySelectorAll('tr'));
    let data = [];
    
    rows.forEach(row => {
        const cells = Array.from(row.querySelectorAll('td, th'));
        data.push(cells.map(cell => cell.textContent));
    });
    
    if (format === 'csv') {
        const csv = data.map(row => row.join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'data.csv';
        a.click();
    }
} 