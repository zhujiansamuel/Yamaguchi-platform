<?php

namespace fast;

/**
 * 中国語をピンインに変換するクラス
 */
class Pinyin
{

    /**
     * 文字のピンインを取得
     * @param string  $chinese   中国語漢字
     * @param boolean $onlyfirst ピンインの頭文字のみ返すかどうか
     * @param string  $delimiter 区切り文字
     * @param bool    $ucfirst   頭文字を大文字にするかどうか
     * @return string
     */
    public static function get($chinese, $onlyfirst = false, $delimiter = '', $ucfirst = false)
    {

        $pinyin = new \Overtrue\Pinyin\Pinyin();
        if ($onlyfirst) {
            $result = $pinyin->abbr($chinese, $delimiter);
        } else {
            $result = $pinyin->permalink($chinese, $delimiter);
        }
        if ($ucfirst) {
            $pinyinArr = explode($delimiter, $result);
            $result = implode($delimiter, array_map('ucfirst', $pinyinArr));
        }

        return $result;
    }

}
