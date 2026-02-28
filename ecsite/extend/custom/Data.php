<?php
namespace custom;

use think\Cache;
use think\Exception;

class  Data  
{

    private static $methodArr = ['name'];

    private static $method = '';

    public static function name($model_name='',$data = [], $extend = [])
    {
        $str = str_replace('_',' ', $model_name);
        $str = ucwords($str);
        $str = str_replace(' ','', $str);

        $Obj = '\\app\\common\\model\\'.$str;
        if(class_exists($Obj)){
            return new Base( new $Obj(), $data, $extend);
        }

        $Obj = '\\app\\admin\\model\\'.$str;
        if(class_exists($Obj)){
            return new Base( new $Obj(), $data, $extend);
        }
        throw new Exception('該当するモデルクラスがありません');
    }

}