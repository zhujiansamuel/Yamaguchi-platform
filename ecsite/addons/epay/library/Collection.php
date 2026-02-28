<?php

namespace addons\epay\library;

class Collection extends \Yansongda\Supports\Collection
{

    /**
     * 作成 Collection インスタンス
     * @access public
     * @param  array $items データ
     * @return static
     */
    public static function make($items = [])
    {
        return new static($items);
    }
}
