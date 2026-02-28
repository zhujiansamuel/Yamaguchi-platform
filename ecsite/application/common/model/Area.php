<?php

namespace app\common\model;

use think\Cache;
use think\Model;

/**
 * エリアデータモデル
 */
class Area extends Model
{

    /**
     * 経度・緯度から現在のエリア情報を取得
     *
     * @param string $lng 経度
     * @param string $lat 緯度
     * @return Area 都市情報
     */
    public static function getAreaFromLngLat($lng, $lat, $level = 3)
    {
        $namearr = [1 => 'geo:province', 2 => 'geo:city', 3 => 'geo:district'];
        $rangearr = [1 => 15000, 2 => 1000, 3 => 200];
        $geoname = $namearr[$level] ?? $namearr[3];
        $georange = $rangearr[$level] ?? $rangearr[3];
        // 範囲内のIDを読み取るID
        $redis = Cache::store('redis')->handler();
        $georadiuslist = [];
        if (method_exists($redis, 'georadius')) {
            $georadiuslist = $redis->georadius($geoname, $lng, $lat, $georange, 'km', ['WITHDIST', 'COUNT' => 5, 'ASC']);
        }

        if ($georadiuslist) {
            list($id, $distance) = $georadiuslist[0];
        }
        $id = isset($id) && $id ? $id : 3;
        return self::get($id);
    }

    /**
     * 経度・緯度から都道府県を取得
     *
     * @param string $lng 経度
     * @param string $lat 緯度
     * @return Area
     */
    public static function getProvinceFromLngLat($lng, $lat)
    {
        $provincedata = null;
        $citydata = self::getCityFromLngLat($lng, $lat);
        if ($citydata) {
            $provincedata = self::get($citydata['pid']);
        }
        return $provincedata;
    }

    /**
     * 経度・緯度から都市を取得
     *
     * @param string $lng 経度
     * @param string $lat 緯度
     * @return Area
     */
    public static function getCityFromLngLat($lng, $lat)
    {
        $citydata = null;
        $districtdata = self::getDistrictFromLngLat($lng, $lat);
        if ($districtdata) {
            $citydata = self::get($districtdata['pid']);
        }
        return $citydata;
    }

    /**
     * 経度・緯度から地域を取得
     *
     * @param string $lng 経度
     * @param string $lat 緯度
     * @return Area
     */
    public static function getDistrictFromLngLat($lng, $lat)
    {
        $districtdata = self::getAreaFromLngLat($lng, $lat, 3);
        return $districtdata;
    }

}
