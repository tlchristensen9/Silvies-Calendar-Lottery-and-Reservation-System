/**
 * Calendar renderer for Silvies Club Reservation System.
 * Renders a full-year month-by-month grid with color-coded date types:
 *   - Lottery dates (Apr 1 - Aug 7): gold/amber - reservations controlled by draft phases
 *   - Open dates (Dec-Mar): green - any member can book anytime
 *   - Hunting season (Aug 8 - Nov 30): brown - cabin open, no reservation needed
 *   - Blocked dates: red/coral - unavailable (e.g., Annual Meeting)
 * Date types are determined by date ranges, not whole months.
 */

function renderCalendar(containerId, seasonStart, seasonEnd, reservations, canReserve, reserveUrl, calConfig) {
    var container = document.getElementById(containerId);
    if (!container) return;

    var start = new Date(seasonStart + 'T00:00:00');
    var end = new Date(seasonEnd + 'T00:00:00');
    var today = new Date();
    today.setHours(0, 0, 0, 0);

    // Date-based type detection
    var lotteryStart = calConfig.lottery_start ? new Date(calConfig.lottery_start + 'T00:00:00') : new Date(start.getFullYear(), 3, 1);
    var lotteryEnd = calConfig.lottery_end ? new Date(calConfig.lottery_end + 'T00:00:00') : new Date(start.getFullYear(), 7, 7);
    var huntingStart = calConfig.hunting_start ? new Date(calConfig.hunting_start + 'T00:00:00') : new Date(start.getFullYear(), 7, 8);
    var huntingEnd = calConfig.hunting_end ? new Date(calConfig.hunting_end + 'T00:00:00') : new Date(start.getFullYear(), 10, 30);

    function getDateType(d) {
        if (d >= lotteryStart && d <= lotteryEnd) return 'lottery';
        if (d >= huntingStart && d <= huntingEnd) return 'hunting';
        return 'open';
    }

    // Determine the predominant type for a month (for the month block styling)
    function getMonthType(monthIdx) {
        var first = new Date(start.getFullYear(), monthIdx, 1);
        var mid = new Date(start.getFullYear(), monthIdx, 15);
        var t1 = getDateType(first);
        var t2 = getDateType(mid);
        if (t1 === t2) return t1;
        var lastDay = new Date(start.getFullYear(), monthIdx + 1, 0).getDate();
        var counts = { lottery: 0, hunting: 0, open: 0 };
        for (var dd = 1; dd <= lastDay; dd++) {
            counts[getDateType(new Date(start.getFullYear(), monthIdx, dd))]++;
        }
        if (counts.lottery >= counts.hunting && counts.lottery >= counts.open) return 'lottery';
        if (counts.hunting >= counts.open) return 'hunting';
        return 'open';
    }

    // Build a map of reserved dates (stores name + notes + blocked info)
    var reservedMap = {};
    reservations.forEach(function(r) {
        var rStart = new Date(r.start_date + 'T00:00:00');
        var rEnd = new Date(r.end_date + 'T00:00:00');
        var d = new Date(rStart);
        while (d <= rEnd) {
            var key = dateToKey(d);
            reservedMap[key] = {
                name: r.is_blocked ? (r.block_label || 'Blocked') : r.member_name,
                notes: r.notes || '',
                is_blocked: r.is_blocked || false,
                block_label: r.block_label || ''
            };
            d.setDate(d.getDate() + 1);
        }
    });

    var year = start.getFullYear();

    // Legend
    var html = '<div class="calendar-legend">';
    html += '<span class="legend-item"><span class="legend-swatch legend-open"></span> Open Booking</span>';
    html += '<span class="legend-item"><span class="legend-swatch legend-lottery"></span> Lottery (Draft)</span>';
    html += '<span class="legend-item"><span class="legend-swatch legend-hunting"></span> Hunting Season</span>';
    html += '<span class="legend-item"><span class="legend-swatch legend-reserved"></span> Reserved</span>';
    html += '<span class="legend-item"><span class="legend-swatch legend-blocked"></span> Blocked</span>';
    html += '</div>';

    // Render all 12 months
    for (var m = 0; m < 12; m++) {
        var monthType = getMonthType(m);
        var monthDate = new Date(year, m, 1);
        var monthName = monthDate.toLocaleString('default', { month: 'long', year: 'numeric' });

        // Check if this is a split month
        var isSplit = false;
        var daysInMonth = new Date(year, m + 1, 0).getDate();
        var firstType = getDateType(new Date(year, m, 1));
        for (var check = 2; check <= daysInMonth; check++) {
            if (getDateType(new Date(year, m, check)) !== firstType) {
                isSplit = true;
                break;
            }
        }

        var typeLabel = '';
        if (isSplit) typeLabel = ' — Mixed';
        else if (monthType === 'lottery') typeLabel = ' — Lottery';
        else if (monthType === 'hunting') typeLabel = ' — Hunting Season';
        else typeLabel = ' — Open Booking';

        html += '<div class="calendar-month-block month-' + monthType + '">';
        html += '<div class="calendar-month-title">' + monthName + '<span class="month-type-label">' + typeLabel + '</span></div>';

        if (monthType === 'hunting' && !isSplit) {
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
        for (var d = 1; d <= daysInMonth; d++) {
            var thisDate = new Date(year, m, d);
            var key = dateToKey(thisDate);
            var inSeason = thisDate >= start && thisDate <= end;
            var resInfo = reservedMap[key];
            var isReserved = !!resInfo;
            var isBlocked = resInfo && resInfo.is_blocked;
            var isToday = thisDate.getTime() === today.getTime();
            var dateType = getDateType(thisDate);
            var isHunting = dateType === 'hunting';
            var isLottery = dateType === 'lottery';

            var classes = 'calendar-day';
            if (!inSeason) classes += ' outside';
            if (isBlocked) classes += ' blocked';
            else if (isReserved) classes += ' reserved';
            if (isToday) classes += ' today';
            if (isHunting) classes += ' hunting-day';
            if (isLottery && !isReserved && !isBlocked) classes += ' lottery-day';
            if (inSeason && !isReserved && !isBlocked && !isHunting && canReserve) classes += ' available';

            var content = '<span class="day-num">' + d + '</span>';
            if (isBlocked) {
                content += '<span class="res-label blocked-label">' + (resInfo.block_label || 'Blocked') + '</span>';
            } else if (isReserved) {
                content += '<span class="res-label">' + resInfo.name + '</span>';
                if (resInfo.notes) {
                    content += '<span class="res-notes">' + resInfo.notes + '</span>';
                }
            }

            // Tooltip
            var titleAttr = '';
            if (isBlocked) {
                titleAttr = ' title="' + (resInfo.block_label || 'Blocked') + '"';
            } else if (isReserved && resInfo.notes) {
                titleAttr = ' title="' + resInfo.name + ': ' + resInfo.notes.replace(/"/g, '&quot;') + '"';
            } else if (isReserved) {
                titleAttr = ' title="' + resInfo.name + '"';
            }

            // Click to start reservation (not for hunting, reserved, or blocked days)
            var onClick = '';
            if (inSeason && !isReserved && !isBlocked && !isHunting && canReserve && reserveUrl) {
                var isoDate = key;
                var endDefault = new Date(thisDate);
                endDefault.setDate(endDefault.getDate() + 6);
                var maxEnd = end < endDefault ? end : endDefault;
                onClick = ' onclick="window.location=\'' + reserveUrl + '?start=' + isoDate + '&end=' + dateToKey(maxEnd) + '\'"';
            }

            html += '<div class="' + classes + '"' + titleAttr + onClick + '>' + content + '</div>';
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
