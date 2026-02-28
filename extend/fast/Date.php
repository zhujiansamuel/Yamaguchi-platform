<?php

namespace fast;

use DateTime;
use DateTimeZone;

/**
 * 日付と時刻の処理クラス
 */
class Date
{
    const YEAR = 31536000;
    const MONTH = 2592000;
    const WEEK = 604800;
    const DAY = 86400;
    const HOUR = 3600;
    const MINUTE = 60;

    /**
     * 2つのタイムゾーン間の差分時間を計算,単位は秒
     *
     * $seconds = self::offset('America/Chicago', 'GMT');
     *
     * [!!] A list of time zones that PHP supports can be found at
     * <http://php.net/timezones>.
     *
     * @param string $remote timezone that to find the offset of
     * @param string $local  timezone used as the baseline
     * @param mixed  $now    UNIX timestamp or date string
     * @return  integer
     */
    public static function offset($remote, $local = null, $now = null)
    {
        if ($local === null) {
            // Use the default timezone
            $local = date_default_timezone_get();
        }
        if (is_int($now)) {
            // Convert the timestamp into a string
            $now = date(DateTime::RFC2822, $now);
        }
        // Create timezone objects
        $zone_remote = new DateTimeZone($remote);
        $zone_local = new DateTimeZone($local);
        // Create date objects from timezones
        $time_remote = new DateTime($now, $zone_remote);
        $time_local = new DateTime($now, $zone_local);
        // Find the offset
        $offset = $zone_remote->getOffset($time_remote) - $zone_local->getOffset($time_local);
        return $offset;
    }

    /**
     * 2つのタイムスタンプ間の経過時間を計算
     *
     * $span = self::span(60, 182, 'minutes,seconds'); // array('minutes' => 2, 'seconds' => 2)
     * $span = self::span(60, 182, 'minutes'); // 2
     *
     * @param int    $remote timestamp to find the span of
     * @param int    $local  timestamp to use as the baseline
     * @param string $output formatting string
     * @return  string   when only a single output is requested
     * @return  array    associative list of all outputs requested
     * @from https://github.com/kohana/ohanzee-helpers/blob/master/src/Date.php
     */
    public static function span($remote, $local = null, $output = 'years,months,weeks,days,hours,minutes,seconds')
    {
        // Normalize output
        $output = trim(strtolower((string)$output));
        if (!$output) {
            // Invalid output
            return false;
        }
        // Array with the output formats
        $output = preg_split('/[^a-z]+/', $output);
        // Convert the list of outputs to an associative array
        $output = array_combine($output, array_fill(0, count($output), 0));
        // Make the output values into keys
        extract(array_flip($output), EXTR_SKIP);
        if ($local === null) {
            // Calculate the span from the current time
            $local = time();
        }
        // Calculate timespan (seconds)
        $timespan = abs($remote - $local);
        if (isset($output['years'])) {
            $timespan -= self::YEAR * ($output['years'] = (int)floor($timespan / self::YEAR));
        }
        if (isset($output['months'])) {
            $timespan -= self::MONTH * ($output['months'] = (int)floor($timespan / self::MONTH));
        }
        if (isset($output['weeks'])) {
            $timespan -= self::WEEK * ($output['weeks'] = (int)floor($timespan / self::WEEK));
        }
        if (isset($output['days'])) {
            $timespan -= self::DAY * ($output['days'] = (int)floor($timespan / self::DAY));
        }
        if (isset($output['hours'])) {
            $timespan -= self::HOUR * ($output['hours'] = (int)floor($timespan / self::HOUR));
        }
        if (isset($output['minutes'])) {
            $timespan -= self::MINUTE * ($output['minutes'] = (int)floor($timespan / self::MINUTE));
        }
        // Seconds ago, 1
        if (isset($output['seconds'])) {
            $output['seconds'] = $timespan;
        }
        if (count($output) === 1) {
            // Only a single output was requested, return it
            return array_pop($output);
        }
        // Return array
        return $output;
    }

    /**
     * フォーマット UNIX 人が読みやすい文字列へ変換されたタイムスタンプ
     *
     * @param int    Unix タイムスタンプ
     * @param mixed $local ローカル時刻
     *
     * @return    string    フォーマット済み日付文字列
     */
    public static function human($remote, $local = null)
    {
        $time_diff = (is_null($local) ? time() : $local) - $remote;
        $tense = $time_diff < 0 ? 'after' : 'ago';
        $time_diff = abs($time_diff);
        $chunks = [
            [60 * 60 * 24 * 365, 'year'],
            [60 * 60 * 24 * 30, 'month'],
            [60 * 60 * 24 * 7, 'week'],
            [60 * 60 * 24, 'day'],
            [60 * 60, 'hour'],
            [60, 'minute'],
            [1, 'second']
        ];
        $name = 'second';
        $count = 0;

        for ($i = 0, $j = count($chunks); $i < $j; $i++) {
            $seconds = $chunks[$i][0];
            $name = $chunks[$i][1];
            if (($count = floor($time_diff / $seconds)) != 0) {
                break;
            }
        }
        return __("%d $name%s $tense", [$count, ($count > 1 ? 's' : '')]);
    }

    /**
     * 時間オフセットに基づくUnixタイムスタンプ
     *
     * @param string $type     時間タイプ，デフォルトはday，選択可能minute,hour,day,week,month,quarter,year
     * @param int    $offset   時間オフセット量 デフォルトは0，正数は現在のtype以降を示す，負数は現在のtype以前を示す
     * @param string $position 時間の開始または終了，デフォルトはbegin，選択可能：前(begin,start,first,front)，end
     * @param int    $year     基準年，デフォルトはnull，現在の年を基準とする
     * @param int    $month    基準月，デフォルトはnull，現在の月を基準とする
     * @param int    $day      基準日，デフォルトはnull，現在の日を基準とする
     * @param int    $hour     基準時，デフォルトはnull，現在の時刻を基準とする
     * @param int    $minute   基準分，デフォルトはnull，現在の分を基準とする
     * @return int 処理後のUnixタイムスタンプ
     */
    public static function unixtime($type = 'day', $offset = 0, $position = 'begin', $year = null, $month = null, $day = null, $hour = null, $minute = null)
    {
        $year = is_null($year) ? date('Y') : $year;
        $month = is_null($month) ? date('m') : $month;
        $day = is_null($day) ? date('d') : $day;
        $hour = is_null($hour) ? date('H') : $hour;
        $minute = is_null($minute) ? date('i') : $minute;
        $position = in_array($position, array('begin', 'start', 'first', 'front'));

        $baseTime = mktime(0, 0, 0, $month, $day, $year);

        switch ($type) {
            case 'minute':
                $time = $position ? mktime($hour, $minute + $offset, 0, $month, $day, $year) : mktime($hour, $minute + $offset, 59, $month, $day, $year);
                break;
            case 'hour':
                $time = $position ? mktime($hour + $offset, 0, 0, $month, $day, $year) : mktime($hour + $offset, 59, 59, $month, $day, $year);
                break;
            case 'day':
                $time = $position ? mktime(0, 0, 0, $month, $day + $offset, $year) : mktime(23, 59, 59, $month, $day + $offset, $year);
                break;
            case 'week':
                $weekIndex = date("w", $baseTime);
                $time = $position ?
                    strtotime($offset . " weeks", strtotime(date('Y-m-d', strtotime("-" . ($weekIndex ? $weekIndex - 1 : 6) . " days", $baseTime)))) :
                    strtotime($offset . " weeks", strtotime(date('Y-m-d 23:59:59', strtotime("+" . (6 - ($weekIndex ? $weekIndex - 1 : 6)) . " days", $baseTime))));
                break;
            case 'month':
                $_timestamp = mktime(0, 0, 0, $month + $offset, 1, $year);
                $time = $position ? $_timestamp : mktime(23, 59, 59, $month + $offset, self::days_in_month(date("m", $_timestamp), date("Y", $_timestamp)), $year);
                break;
            case 'quarter':
                $quarter = ceil(date('n', $baseTime) / 3) + $offset;
                $month = $quarter * 3;
                $offset_year = ceil($month/12) - 1;
                $year = $year + $offset_year;
                $month = $month - ($offset_year * 12);
                $time = $position ?
                    mktime(0, 0, 0, $month-2, 1, $year) :
                    mktime(23, 59, 59, $month, self::days_in_month($month, $year), $year);
                break;
            case 'year':
                $time = $position ? mktime(0, 0, 0, 1, 1, $year + $offset) : mktime(23, 59, 59, 12, 31, $year + $offset);
                break;
            default:
                $time = mktime($hour, $minute, 0, $month, $day, $year);
                break;
        }
        return $time;
    }

    /**
     * 指定した年月の日数を取得
     * @param int $month
     * @param int $year
     * @return false|int|string
     */
    public static function days_in_month($month, $year)
    {
        if (function_exists("cal_days_in_month")) {
            return cal_days_in_month(CAL_GREGORIAN, $month, $year);
        } else {
            return date('t', mktime(0, 0, 0, $month, 1, $year));
        }
    }
}
