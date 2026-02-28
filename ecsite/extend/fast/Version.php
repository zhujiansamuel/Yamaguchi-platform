<?php

namespace fast;

/**
 * バージョンの検出と比較
 */
class Version
{

    /**
     * バージョンが要件を満たしているかをデータ内で検査
     *
     * @param string $version
     * @param array  $data
     * @return bool
     */
    public static function check($version, $data = [])
    {
        //バージョン番号を.で区切る
        $data = is_array($data) ? $data : [$data];
        if ($data) {
            if (in_array("*", $data) || in_array($version, $data)) {
                return true;
            }
            $ver = explode('.', $version);
            if ($ver) {
                $versize = count($ver);
                //許可されたバージョンを検証
                foreach ($data as $m) {
                    $c = explode('.', $m);
                    if (!$c || $versize != count($c)) {
                        continue;
                    }
                    $i = 0;
                    foreach ($c as $a => $k) {
                        if (!self::compare($ver[$a], $k)) {
                            continue 2;
                        } else {
                            $i++;
                        }
                    }
                    if ($i == $versize) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    /**
     * 2つのバージョン番号を比較
     *
     * @param string $v1
     * @param string $v2
     * @return boolean
     */
    public static function compare($v1, $v2)
    {
        if ($v2 == "*" || $v1 == $v2) {
            return true;
        } else {
            $values = [];
            $k = explode(',', $v2);
            foreach ($k as $v) {
                if (strpos($v, '-') !== false) {
                    list($start, $stop) = explode('-', $v);
                    for ($i = $start; $i <= $stop; $i++) {
                        $values[] = $i;
                    }
                } else {
                    $values[] = $v;
                }
            }
            return in_array($v1, $values) ? true : false;
        }
    }
}
