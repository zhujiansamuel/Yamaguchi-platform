<?php

namespace custom;

class Base
{
    

    private $limit = 10;

    private $setWhere = [];

    protected $setArrayMap = null;

    protected $seToArray = null;

    protected $setParams = null;

    protected $editData = [];

    private $setOtherFunction = null;

    private $params = [];
    
    private $notlimit = null;
    
    private $dbfields = null;
    
    protected $_error = '';
    //データセット
    protected $DataSet = [];

    /**
     * @var array インスタンス
     */
    protected static $extendArr = [];

    private $noDisabledModel = [];


    /**
     * 初期化
     * @access public
     * @param  array $options 設定配列
     */
    public static function init(array $options = [])
    {
        if (isset(self::$extendArr) && empty(self::$extendArr)) {

            self::$extendArr = $options;
        }
        $ClassName = get_called_class();
        return new $ClassName;
    }

    public function __construct($obj,$options = [], $extend = [])
    {
        if (isset(self::$extendArr) && empty(self::$extendArr)) {
            self::$extendArr = $options;
        }
        $this->obj = $obj;
    }

    public function wlist($extend = [], $is_array = true)
    {
        $extend['order'] = 'p.weigh desc';
        return $this->lists($extend, $is_array);
    }

    public function wilist($extend = [], $is_array = true)
    {
        $this->imageDominName = true;
        $extend['order'] = 'p.weigh desc';
        return $this->lists($extend, $is_array);
    }

    public function __call($name, $arguments) {
        switch ($name) {
            case 'field':
                $param = $arguments[0] ?? '';
                if(strpos($param, 'Fields') === false){
                    $this->field = $param;
                }else{
                    $this->dbfields = $param;
                }
                return $this;
                break;
            case 'where':
                $argumentsCount = count($arguments);
                if($argumentsCount == 1){
                    $this->setWhere = $arguments[0] ?? '';
                }else if($argumentsCount == 2){
                    $this->setWhere = $arguments;
                }
                return $this;
                break;
            case 'handle':
                $value = $arguments[0] ?? '';
                $value = explode(',', $value);
                foreach ($value as $key => $val) {
                    if(method_exists($this->obj, $name.ucfirst($val))){
                        $this->obj->{$name.ucfirst($val)}(self::$extendArr);
                    }
                }
                return $this;
                break;
            case 'verify':
                $value = $arguments[0] ?? '';
                $value = explode(',', $value);
                foreach ($value as $key => $val) {
                    if(method_exists($this->obj, $name.ucfirst($val))){
                        dump($this->params);die;
                        $this->obj->{$name.ucfirst($val)}(self::$extendArr);
                    }
                }
                return $this;
                break;
            case 'db':
                return $this->obj;
                
                break;
            default:
                if(method_exists($this->obj, $name)){
                    $this->obj->{$name}($arguments);
                }
                return $this;
                break;
        }
    }


    /*
     * 一覧を取得
     */
    public function lists($extend = [], $is_array = true)
    {
        $group = $extend['group'] ?? null;
        $with = $extend['with'] ?? null;
        $join = $extend['join'] ?? [];
        if(isset(self::$extendArr['limit']) && self::$extendArr['limit']){
            $limit = self::$extendArr['limit'];
        }else{
            $limit =  $this->limit;
        }
        
        $order = $extend['order'] ?? 'p.id desc';
        $where = $params = $list = [];
        $type = $extend['type'] ?? 'paginate';
        $having = $extend['having'] ?? null;
        if($this->dbfields){
            $Db_fields = $this->dbfields;
        }else{
            $Db_fields = 'DbFields';
        }
        $field = isset($extend['field']) ? $extend['field'] : (property_exists($this->obj, $Db_fields) ? $this->obj->{$Db_fields} : '*');
        if($join && $field != '*'){
            $fields = explode(',', $field);
            $fieldString = [];
            foreach ($fields as $key => $val) {
                $fieldString[]= 'p.'.trim($val);
            }
            $field = join(',', $fieldString);
        }
        if(isset($this->field)){
            $field = $this->field;
        }
        // if(!in_array(get_called_class(), $this->noDisabledModel)){
        //     $where['p.disabled'] = 0;
        // }
        if(isset(self::$extendArr['id']) && self::$extendArr['id']){
            $where['id'] = self::$extendArr['id'];
        }

        $data= $this->obj->alias('p')->field($field)
          ->with($with)
          ->join($join)
          ->where($where)
          ->where($this->setWhere)
          ->order($order)->group($group);
          
        if($having){
            $data = $data->having($having);
        }

        if($this->notlimit  || (isset(self::$extendArr['id']) && self::$extendArr['id'])){
            $data = $data->select();
        }else{
            if($type == 'paginate'){
                $data = $data->paginate($limit);
                if(isset($this->imageDominName)){
                    $domainName = config('other.WEB_DOMAIN_NAME');
                    $data = $data->each(function($item) use($domainName){
                        $item['image'] = $domainName . $item['image']; 
                        return $item;
                    });
                }
            }else{
                $data = $data->page(self::$extendArr['page'] ?? 1, $limit)->select();
            }
        }
        

        $totalPage = 0;
        if($data){
            if($type == 'select' || $this->notlimit){
                $list = $data->toArray();
            }else if(isset(self::$extendArr['id']) && self::$extendArr['id']){
                $list = $data;
            }else if($type == 'paginate'){
                $list = $data->all();
                //総ページ数
                $params['totalPage'] = $data->lastPage();
                //現在のページ数
                $params['currentPage'] = $data->currentPage();
                //総件数
                $params['total'] = $data->total();
            }

            if($this->seToArray){
                if(method_exists($this->obj, $this->seToArray)){
                    $list = $this->obj->{$this->seToArray}($list);
                }
            }

            if($this->setArrayMap){
                $list =  array_map($this->setArrayMap, $list);
            }

        }

        $this->setWhere = $this->setArrayMap = [];

        if(isset(self::$extendArr['id']) && self::$extendArr['id']){
            return  $list[0] ?? [];
        }

        $params['list'] = $list;

        unset($list, $data);

        if(!$is_array){
            $this->params = $params;
            return $this;
        }
        
        return $params;
    }

    public function toLists($extend = [])
    {
        $list = $this->lists($extend);
        return $list['list'];
    }

    public function lists_column($key = null, $array = null, $extend = [])
    {
        $list = $this->lists($extend);
        if(!$key){
            return $list;
        }
        if($array){
            return array_column($list['list'], $array, $key);
        }
        return array_column($list['list'], $key);
    }

    public function infos($extend = [])
    {
        if(!$this->setWhere){
            return [];
        }
        $where = $this->setWhere;
        // if(!in_array(get_called_class(), $this->noDisabledModel)){
        //     $where['p.disabled'] = 0;
        // }
        $with = $extend['with'] ?? null;
        $join = $extend['join'] ?? [];
        $order = $extend['order'] ?? 'p.id desc';
        if($this->dbfields){
            $Db_fields = $this->dbfields;
        }else{
            $Db_fields = 'Db_fields';
        }
        $field = isset($extend['field']) ? $extend['field'] : (property_exists($this->obj, $Db_fields) ? $this->obj->{$Db_fields} : '*');

        if(isset($this->field)){
            $field = $this->field;
        }
        if(($join || $with) && $field != '*'){
            $fields = explode(',', $field);
            $fieldString = [];
            foreach ($fields as $key => $val) {
                $fieldString[]= 'p.'.trim($val);
            }
            $field = join(',', $fieldString);
        }
        $info= $this->obj->alias('p')->field($field)
          ->join($join)
          ->with($with)
          ->where($where)
          ->order($order);
        // if(isset($this->newWhere)){
        //     $info = $info->{$this->newWhere};
        // }
        $info = $info->find();
          //echo $this->getLastSql();die;
        if($info){
            $info = $info->toArray();
            if($this->seToArray){
                if(method_exists($this, $this->seToArray)){
                    $info = $this->{$this->seToArray}($info);
                }
            }
            //$this->DataSet['info'] = $info;
            if($this->setParams){
                $setParams = is_array($this->setParams) ? $this->setParams : explode(',', $this->setParams);
                foreach ($setParams as $key => $val) {
                    if(method_exists($this, $val)){
                        $res = $this->{$val}($info);
                        if($res){
                            $info[$val] = $res;
                        }
                    }
                }
            }
        }

        $this->setWhere = [];
        return $info;
    }

    public function counts($extend = [])
    {
        if(!$this->setWhere){
            return [];
        }
        $where = $this->setWhere;
        // if(!in_array(get_called_class(), $this->noDisabledModel)){
        //     $where['p.disabled'] = 0;
        // }
        $join = $extend['join'] ?? [];
        $count= $this->alias('p')
          ->join($join)
          ->where($where)
          ->count();
          //echo $this->getLastSql();die;

        $this->setWhere = [];
        return $count;
    }

    /*
     * データを更新
     */
    public function updateData($data = [], $extend = [])
    {
        $data = $data ? $data : $this->obj->editData;
        if(!$data){
            return false;
        }

        if((isset($data['id']) && $data['id']) || $this->setWhere){
            if($this->setWhere){
                $where = $this->setWhere;
            }else{
                $id = $data['id'];
                unset($data['id']);
                $where = ['id' => $id];
            }
            $res = $this->obj->where($where)->update($data);
            $res = $res ? ($where['id'] ?? true) : false;
        }else{
            $res = $this->addData($data, $extend);
        }
        $this->setWhere = [];
        if($res){
            if($this->setOtherFunction){
                self::$extendArr = array_merge(self::$extendArr, $this->setWhere);
                //$this->params['']
                $this->IsExistsFunction($this->setOtherFunction);
                unset($this->setOtherFunction);
            }
            return $res;
        }
        return false;
    }

    /*
     * データを一括更新
     */
    public function updateAll($data = [], $extend = [])
    {
        $res = $this->saveAll($data);
        if($res){
            return $res;
        }
        return false;
    }

    public function addData($data = [], $extend = [])
    {
        $data['createtime'] = time();
        $res = $this->create($data);
        if($this->getLastInsID()){
            return $this->getLastInsID();
        }
        return false;
    }

    public function addExtend($extend = [])
    {
        self::$extendArr = array_merge(self::$extendArr, $extend);
        return $this;
    }

    public function setArrayMap($function = [])
    {
        if($function){
            $this->setArrayMap = $function;
        }
        
        return $this;
    }
    
    public function notlimit()
    {
        $this->notlimit = true;
        return $this;
    }
    
    public function dbfields($filed = '')
    {
        if($filed){
            $this->dbfields = $filed;
        }
        return $this;
    }

    public function seToArray($functionName = '')
    {
        if($functionName){
            $this->seToArray = $functionName;
        }
        
        return $this;
    }

    public function setParams($functionName = '')
    {
        if($functionName){
            $this->setParams = $functionName;
        }
        
        return $this;
    }

    //他のテーブルデータを処理
    public function handleOtherDb($function = '', $front = true)
    {
        if($front){
            $this->IsExistsFunction($function);
        }else{
            $this->setOtherFunction = $function;
        }
        return $this;
    }

    private function IsExistsFunction($function = '')
    {
        if($function){
            if(method_exists($this, $function)){
                $this->{$function}();
            }
        }
    }

    protected function getFields()
    {
        //$this->Db_fields = 
        return $this;
    }

    protected function setMillisecond($time = '')
    {
        return isset($time) ? $time/1000 : 0;
    }

    protected function getTableInfo($table = '')
    {
        /*if(!$table){

        }
        $prefix = config('database.prefix');
        $data = Db::query('SHOW FULL COLUMNS FROM '.$this->prefix.$table);
        return $data;*/
    }
    
    /**
     * エラーメッセージを設定
     *
     * @param $error エラーメッセージ
     * @return Auth
     */
    public function setError($error)
    {
        $this->_error = $error;
        return $this;
    }

    /**
     * エラーメッセージを取得
     * @return string
     */
    public function getError()
    {
        return \custom\ConfigStatus::ERROR_LIST[$this->_error] ?? (property_exists($this, 'ErrorList') ? $this->ErrorList[$this->_error] ?? "" : $this->_error );
    }
    
    public function verifi($name='Empty')
    {
        if($name){
            $name = explode(',', $name);
            foreach ($name as $key => $val) {
                if(method_exists($this, 'verifi'.ucfirst($val))){
                    $this->{'verifi'.ucfirst($val)}();
                    if($this->_error){
                        throw new \think\Exception($this->getError());
                        return false;
                    }
                }
            }
            
        }
        return $this; 
    }
    
    /*
     * マーケティング活動
    */
    public function marketing($name='')
    {
        if($name){
            $name = explode(',', $name);
            foreach ($name as $key => $val) {
                if(method_exists($this, $val)){
                    $this->{$val}();
                }
            }
            
            if($this->_error){
                throw new \think\Exception($this->getError());
                return false;
            }
        }
        return $this; 
    }

}
