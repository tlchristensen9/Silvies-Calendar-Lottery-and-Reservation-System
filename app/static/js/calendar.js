/**
 * Calendar renderer for Silvies Club Reservation System.
 * Renders a full-year month-by-month grid with color-coded month types:
 *   - Lottery months (May-Jun): gold/amber - reservations controlled by draft phases
 *   - Open months (Jul, Dec-Apr): green - any member can book anytime
 *   - Hunting season (Aug-Nov): brown - cabin open, no reservation needed
 */

function renderCalendar(containerId, seasonStart, seasonEnd, reservations, canReserve, reserveUrl, monthConfig) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const start = new Date(seasonStart + 'T00:00:00');
    const end = new Date(seasonEnd + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Month type lookups (months are 1-indexed in config, JS uses 0-indexed)
    const lotteryMonths = new Set((monthConfig.lottery_months || [5, 6]));
    const huntingMonths = new Set((monthConfig.hunting_months || [8, 9, 10, 11]));
    const openMonths = new Set((monthConfig.open_months || [7, 12, 1, 2, 3, 4]));

    function getMonthType(month1Indexed) {
        if (lotteryMonths.has(month1Indexed)) return 'lottery';
        if (huntingMonths.has(month1Indexed)) return 'hunting';
        return 'open';
    }

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

    const year = start.getFullYear();

    // Legend
    var html = '<div class="calendar-legend">';
    html += '<span class="legend-item"><span class="legend-swatch legend-open"></span> Open Booking</span>';
    html += '<span class="legend-item"><span class="legend-swatch legend-lottery"></span> Lottery (Draft)</span>';
    html += '<span class="legend-item"><span class="legend-swatch legend-hunting"></span> Hunting Season</span>';
    html += '<span class="legend-item"><span class="legend-swatch legend-reserved"></span> Reserved</span>';
    html += '</div>';

    // Render all 12 months
    for (var m = 0; m < 12; m++) {
        var month1 = m + 1; // 1-indexed month
        var monthType = getMonthType(month1);
        var monthDate = new Date(year, m, 1);
        var monthName = monthDate.toLocaleString('default', { month: 'long', year: 'numeric' });

        var typeLabel = '';
        if (monthType === 'lottery') typeLabel = ' — Lottery';
        else if (monthType === 'hunting') typeLabel = ' — Hunting Season';
        else typeLabel = ' — Open Booking';

        html += '<div class="calendar-month-block month-' + monthType + '">';
        html += '<div class="calendar-month-title">' + monthName + '<span class="month-type-label">' + typeLabel + '</span></div>';

        if (monthType === 'hunting') {
            html += '<div class="hunting-notice">Cabin open — no reservation needed</div>';
        }

        html += '<div class="calendar-grid">';

        // Day headers
        var days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        for (var di = 0; di < days.length; di++) {
            html += '<div class="calendar-header">' + days[di] + '</div>';
        }

        // Leading blank cells
        var firstDay = new Date(year, m, 1).getDay();
        for (var i = 0; i < firstDay; i++) {
            html += '<div class="calendar-day outside"></div>';
        }

        // Days of the month
        var daysInMonth = new Date(year, m + 1, 0).getDate();
        for (var d = 1; d <= daysInMonth; d++) {
            var thisDate = new Date(year, m, d);
            var key = dateToKey(thisDate);
            var inSeason = thisDate >= start && thisDate <= end;
            var isReserved = reservedMap[key];
            var isToday = thisDate.getTime() === today.getTime();
            var isHunting = monthType === 'hunting';

            var classes = 'calendar-day';
            if (!inSeason) classes += ' outside';
            if (isReserved) classes += ' reserved';
            if (isToday) classes += ' today';
            if (isHunting) classes += ' hunting-day';
            if (inSeason && !isReserved && !isHunting && canReserve) classes += ' available';

            var content = '<span class="day-num">' + d + '</span>';
            if (isReserved) {
                content += '<span class="res-label">' + isReserved + '</span>';
            }

            // Click to start reservation (not for hunting months)
            var onClick = '';
            if (inSeason && !isReserved && !isHunting && canReserve && reserveUrl) {
                var isoDate = key;
                var endDefault = new Date(thisDate);
                endDefault.setDate(endDefault.getDate() + 6);
                var maxEnd = end < endDefault ? end : endDefault;
                onClick = ' onclick="window.location=\'' + reserveUrl + '?start=' + isoDate + '&end=' + dateToKey(maxEnd) + '\'"';
            }

            html += '<div class="' + classes + '"' + onClick + '>' + content + '</div>';
        }

        html += '</div>'; // calendar-grid
        html += '</div>'; // calendar-month-block
    }

    container.innerHTML = html;
}

function dateToKey(d) {
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var day = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + day;
}
