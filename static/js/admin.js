// Изменение статуса заявки на работу
function updateJobStatus(id, status) {
    fetch(`/admin/job/status/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `status=${encodeURIComponent(status)}`
    });
}

// Изменение статуса заявки на услугу
function updateServiceStatus(id, status) {
    fetch(`/admin/service/status/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `status=${encodeURIComponent(status)}`
    });
}