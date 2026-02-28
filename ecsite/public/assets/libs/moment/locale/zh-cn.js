//! moment.js locale configuration
//! locale : Chinese (China) [zh-cn]
//! author : suupic : https://github.com/suupic
//! author : Zeno Zeng : https://github.com/zenozeng
//! author : uu109 : https://github.com/uu109

;(function (global, factory) {
   typeof exports === 'object' && typeof module !== 'undefined'
       && typeof require === 'function' ? factory(require('../moment')) :
   typeof define === 'function' && define.amd ? define(['../moment'], factory) :
   factory(global.moment)
}(this, (function (moment) { 'use strict';

    //! moment.js locale configuration

    var zhCn = moment.defineLocale('zh-cn', {
        months: '1月_2月_3月_4月_5月_6月_7月_8月_9月_10月_十1月_十2月'.split(
            '_'
        ),
        monthsShort: '1月_2月_3月_4月_5月_6月_7月_8月_9月_10月_11月_12月'.split(
            '_'
        ),
        weekdays: '日曜日_月曜日_火曜日_水曜日_木曜日_金曜日_土曜日'.split('_'),
        weekdaysShort: '日曜_月曜_火曜_水曜_木曜_金曜_土曜'.split('_'),
        weekdaysMin: '日_月_火_水_木_金_土'.split('_'),
        longDateFormat: {
            LT: 'HH:mm',
            LTS: 'HH:mm:ss',
            L: 'YYYY/MM/DD',
            LL: 'YYYY年M月D日',
            LLL: 'YYYY年M月D日Ah時mm分',
            LLLL: 'YYYY年M月D日ddddAh時mm分',
            l: 'YYYY/M/D',
            ll: 'YYYY年M月D日',
            lll: 'YYYY年M月D日 HH:mm',
            llll: 'YYYY年M月D日dddd HH:mm',
        },
        meridiemParse: /深夜|早朝|午前|正午|午後|夜/,
        meridiemHour: function (hour, meridiem) {
            if (hour === 12) {
                hour = 0;
            }
            if (meridiem === '深夜' || meridiem === '早朝' || meridiem === '午前') {
                return hour;
            } else if (meridiem === '午後' || meridiem === '夜') {
                return hour + 12;
            } else {
                // '正午'
                return hour >= 11 ? hour : hour + 12;
            }
        },
        meridiem: function (hour, minute, isLower) {
            var hm = hour * 100 + minute;
            if (hm < 600) {
                return '深夜';
            } else if (hm < 900) {
                return '早朝';
            } else if (hm < 1130) {
                return '午前';
            } else if (hm < 1230) {
                return '正午';
            } else if (hm < 1800) {
                return '午後';
            } else {
                return '夜';
            }
        },
        calendar: {
            sameDay: '[今日]LT',
            nextDay: '[明日]LT',
            nextWeek: function (now) {
                if (now.week() !== this.week()) {
                    return '[下]dddLT';
                } else {
                    return '[今]dddLT';
                }
            },
            lastDay: '[昨日]LT',
            lastWeek: function (now) {
                if (this.week() !== now.week()) {
                    return '[前]dddLT';
                } else {
                    return '[今]dddLT';
                }
            },
            sameElse: 'L',
        },
        dayOfMonthOrdinalParse: /\d{1,2}(日|月|週)/,
        ordinal: function (number, period) {
            switch (period) {
                case 'd':
                case 'D':
                case 'DDD':
                    return number + '日';
                case 'M':
                    return number + '月';
                case 'w':
                case 'W':
                    return number + '週';
                default:
                    return number;
            }
        },
        relativeTime: {
            future: '%s後',
            past: '%s前',
            s: '数秒',
            ss: '%d 秒',
            m: '1 分',
            mm: '%d 分',
            h: '1 時間',
            hh: '%d 時間',
            d: '1 日',
            dd: '%d 日',
            w: '1 週',
            ww: '%d 週',
            M: '1 か月',
            MM: '%d か月',
            y: '1 年',
            yy: '%d 年',
        },
        week: {
            // GB/T 7408-1994《データ要素および交換形式·情報交換·日付および時刻の表記方法》とISO 8601:1988同等
            dow: 1, // Monday is the first day of the week.
            doy: 4, // The week that contains Jan 4th is the first week of the year.
        },
    });

    return zhCn;

})));
