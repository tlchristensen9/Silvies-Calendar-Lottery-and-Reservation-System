/**
 * Calendar renderer for Silvies Club Reservation System.
 * Renders a month-by-month grid showing available and reserved dates.
 */

function renderCalendar(containerId, seasonStart, seasonEnd, reservations, canReserve, reserveUrl) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const start = new Date(seasonStart + 'T00:00:00');
    const end = new Date(seasonEnd + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Build a map of reserved dates
    const reservedMap = {};
    reservations.forEach(r => {
        const rStart = new Date(r.start_date + 'T00:00:00');
        const rEnd = new Date(r.end_date + 'T00:00:00');
        const d = new Date(rStart);
        while (d <= rEnd) {
            const key = dateToKey(d);
            reservedMap[key] = r.member_name;
            d.setDate(d.getDate() + 1);
        }
    });

    // Render each month
    let currentMonth = start.getMonth();
    const endMonth = end.getMonth();
    const year = start.getFullYear();

    let html = '';

    for (let m = currentMonth; m <= endMonth; m++) {
        const monthDate = new Date(year, m, 1);
        const monthName = monthDate.toLocaleString('default', { month: 'long', year: 'numeric' });

        html += `<div class="calendar-month-title">${monthName}</div>`;
        html += '<div class="calendar-grid">';

        // Day headers
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        days.forEach(d => {
            html += `<div class="calendar-header">${d}</div>`;
        });

        // Leading blank cells
        const firstDay = new Date(year, m, 1).getDay();
        for (let i = 0; i < firstDay; i++) {
            html += '<div class="calendar-day outside"></div>';
        }

        // Days of the month
        const daysInMonth = new Date(year, m + 1, 0).getDate();
        for (let d = 1; d <= daysInMonth; d++) {
            const thisDate = new Date(year, m, d);
            const key = dateToKey(thisDate);
            const inSeason = thisDate >= start && thisDate <= end;
            const isReserved = reservedMap[key];
            const isToday = thisDate.getTime() === today.getTime();

            let classes = 'calendar-day';
            if (!inSeason) classes += ' outside';
            if (isReserved) classes += ' reserved';
            if (isToday) classes += ' today';
            if (inSeason && !isReserved && canReserve) classes += ' available';

            let content = `<span class="day-num">${d}</span>`;
            if (isReserved) {
                content += `<span class="res-label">${isReserved}</span>`;
            }

            // Click to start reservation
            let onClick = '';
            if (inSeason && !isReserved && canReserve && reserveUrl) {
                const isoDate = key;
                // Calculate default end date (up to 7 days, or end of season)
                const endDefault = new Date(thisDate);
                endDefault.setDate(endDefault.getDate() + 6);
                const maxEnd = end < endDefault ? end : endDefault;
                onClick = ` onclick="window.location='${reserveUrl}?start=${isoDate}&end=${dateToKey(maxEnd)}'"`;
            }

            html += `<div class="${classes}"${onClick}>${content}</div>`;
        }

        html += '</div>';
    }

    container.innerHTML = html;
}

function dateToKey(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
}
