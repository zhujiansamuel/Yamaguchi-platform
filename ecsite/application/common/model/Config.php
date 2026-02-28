<?php

namespace app\common\model;

use think\Model;

/**
 * モデルを設定
 */
class Config extends Model
{

    // テーブル名,プレフィックスを含まない
    protected $name = 'config';
    // タイムスタンプフィールドを自動書き込み
    protected $autoWriteTimestamp = false;
    // タイムスタンプフィールド名を定義
    protected $createTime = false;
    protected $updateTime = false;
    // 追加属性
    protected $append = [
        'extend_html'
    ];
    protected $type = [
        'setting' => 'json',
    ];

    /**
     * 設定タイプを読み込む
     * @return array
     */
    public static function getTypeList()
    {
        $typeList = [
            'string'        => __('String'),
            'password'      => __('Password'),
            'text'          => __('Text'),
            'editor'        => __('Editor'),
            'number'        => __('Number'),
            'date'          => __('Date'),
            'time'          => __('Time'),
            'datetime'      => __('Datetime'),
            'datetimerange' => __('Datetimerange'),
            'select'        => __('Select'),
            'selects'       => __('Selects'),
            'image'         => __('Image'),
            'images'        => __('Images'),
            'file'          => __('File'),
            'files'         => __('Files'),
            'switch'        => __('Switch'),
            'checkbox'      => __('Checkbox'),
            'radio'         => __('Radio'),
            'city'          => __('City'),
            'selectpage'    => __('Selectpage'),
            'selectpages'   => __('Selectpages'),
            'array'         => __('Array'),
            'custom'        => __('Custom'),
        ];
        return $typeList;
    }

    public static function getRegexList()
    {
        $regexList = [
            'required' => '必須',
            'digits'   => '数値',
            'letters'  => '英字',
            'date'     => '日付',
            'time'     => '時間',
            'email'    => 'メールアドレス',
            'url'      => 'URL',
            'qq'       => 'QQ記号',
            'IDcard'   => '身分証明書',
            'tel'      => '固定電話',
            'mobile'   => '携帯番号',
            'zipcode'  => '郵便番号',
            'chinese'  => '中国語',
            'username' => 'ユーザー名',
            'password' => 'パスワード'
        ];
        return $regexList;
    }

    public function getExtendHtmlAttr($value, $data)
    {
        $result = preg_replace_callback("/\{([a-zA-Z]+)\}/", function ($matches) use ($data) {
            if (isset($data[$matches[1]])) {
                return $data[$matches[1]];
            }
        }, $data['extend']);
        return $result;
    }

    /**
     * カテゴリグループ一覧を読み込む
     * @return array
     */
    public static function getGroupList()
    {
        $groupList = config('site.configgroup');
        foreach ($groupList as $k => &$v) {
            $v = __($v);
        }
        return $groupList;
    }

    public static function getArrayData($data)
    {
        if (!isset($data['value'])) {
            $result = [];
            foreach ($data as $index => $datum) {
                $result['field'][$index] = $datum['key'];
                $result['value'][$index] = $datum['value'];
            }
            $data = $result;
        }
        $fieldarr = $valuearr = [];
        $field = $data['field'] ?? ($data['key'] ?? []);
        $value = $data['value'] ?? [];
        foreach ($field as $m => $n) {
            if ($n != '') {
                $fieldarr[] = $field[$m];
                $valuearr[] = $value[$m];
            }
        }
        return $fieldarr ? array_combine($fieldarr, $valuearr) : [];
    }

    /**
     * 文字列を解析してキー値配列にする
     * @param string $text
     * @return array
     */
    public static function decode($text, $split = "\r\n")
    {
        $content = explode($split, $text);
        $arr = [];
        foreach ($content as $k => $v) {
            if (stripos($v, "|") !== false) {
                $item = explode('|', $v);
                $arr[$item[0]] = $item[1];
            }
        }
        return $arr;
    }

    /**
     * キー値配列を文字列に変換
     * @param array $array
     * @return string
     */
    public static function encode($array, $split = "\r\n")
    {
        $content = '';
        if ($array && is_array($array)) {
            $arr = [];
            foreach ($array as $k => $v) {
                $arr[] = "{$k}|{$v}";
            }
            $content = implode($split, $arr);
        }
        return $content;
    }

    /**
     * ローカルアップロードの設定情報
     * @return array
     */
    public static function upload()
    {
        $uploadcfg = config('upload');

        $uploadurl = request()->module() ? $uploadcfg['uploadurl'] : ($uploadcfg['uploadurl'] === 'ajax/upload' ? 'index/' . $uploadcfg['uploadurl'] : $uploadcfg['uploadurl']);

        if (!preg_match("/^((?:[a-z]+:)?\/\/)(.*)/i", $uploadurl) && substr($uploadurl, 0, 1) !== '/') {
            $uploadurl = url($uploadurl, '', false);
        }
        $uploadcfg['fullmode'] = isset($uploadcfg['fullmode']) && $uploadcfg['fullmode'];
        $uploadcfg['thumbstyle'] = $uploadcfg['thumbstyle'] ?? '';

        $upload = [
            'cdnurl'     => $uploadcfg['cdnurl'],
            'uploadurl'  => $uploadurl,
            'bucket'     => 'local',
            'maxsize'    => $uploadcfg['maxsize'],
            'mimetype'   => $uploadcfg['mimetype'],
            'chunking'   => $uploadcfg['chunking'],
            'chunksize'  => $uploadcfg['chunksize'],
            'savekey'    => $uploadcfg['savekey'],
            'multipart'  => [],
            'multiple'   => $uploadcfg['multiple'],
            'fullmode'   => $uploadcfg['fullmode'],
            'thumbstyle' => $uploadcfg['thumbstyle'],
            'storage'    => 'local'
        ];
        return $upload;
    }

    /**
     * 設定ファイルを更新
     */
    public static function refreshFile()
    {
        //権限がない場合は設定を変更できません
        if (!\app\admin\library\Auth::instance()->check('general/config/edit')) {
            return false;
        }
        $config = [];
        $configList = self::all();
        foreach ($configList as $k => $v) {
            $value = $v->toArray();
            if (in_array($value['type'], ['selects', 'checkbox', 'images', 'files'])) {
                $value['value'] = explode(',', $value['value']);
            }
            if ($value['type'] == 'array') {
                $value['value'] = (array)json_decode($value['value'], true);
            }
            $config[$value['name']] = $value['value'];
        }
        file_put_contents(
            CONF_PATH . 'extra' . DS . 'site.php',
            '<?php' . "\n\nreturn " . var_export($config, true) . ";\n"
        );
        return true;
    }

}
