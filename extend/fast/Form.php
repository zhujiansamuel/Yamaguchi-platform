<?php

namespace fast;

use ArrayAccess;

/**
 * フォーム要素生成
 * @class   Form
 * @package fast
 * @method static string token() 生成Token
 * @method static string label(string $name, string $value = null, array $options = []) labelラベル
 * @method static string input($type, $name, string $value = null, array $options = []) タイプに応じてテキストボックスを生成
 * @method static string text(string $name, string $value = null, array $options = []) 通常テキストボックス
 * @method static string password(string $name, array $options = []) パスワードテキストボックス
 * @method static string hidden(string $name, string $value = null, array $options = []) 非表示テキストボックス
 * @method static string email(string $name, string $value = null, array $options = []) Emailテキストボックス
 * @method static string url(string $name, string $value = null, array $options = []) URLテキストボックス
 * @method static string file(string $name, array $options = []) ファイルアップロードコンポーネント
 * @method static string textarea(string $name, string $value = null, array $options = []) 複数行テキストボックス
 * @method static string editor(string $name, string $value = null, array $options = []) リッチテキストエディター
 * @method static string select(string $name, array $list = [], string $selected = null, array $options = []) ドロップダウンリストコンポーネント
 * @method static string selects(string $name, array $list = [], string $selected = null, array $options = []) ドロップダウンリストコンポーネント(複数選択)
 * @method static string selectpicker(string $name, array $list = [], string $selected = null, array $options = []) ドロップダウンリストコンポーネント(フレンドリー)
 * @method static string selectpickers(string $name, array $list = [], string $selected = null, array $options = []) ドロップダウンリストコンポーネント(フレンドリー)(複数選択)
 * @method static string selectpage(string $name, string $value, string $url, string $field = null, string $primaryKey = null, array $options = []) 動的ドロップダウンリストコンポーネント
 * @method static string selectpages(string $name, string $value, string $url, string $field = null, string $primaryKey = null, array $options = []) 動的ドロップダウンリストコンポーネント(複数選択)
 * @method static string citypicker(string $name, string $value, array $options = []) 都市選択コンポーネント
 * @method static string switcher(string $name, string $value, array $options = []) トグルコンポーネント
 * @method static string datepicker(string $name, string $value, array $options = []) 日付選択コンポーネント
 * @method static string timepicker(string $name, string $value, array $options = []) 時間選択コンポーネント
 * @method static string datetimepicker(string $name, string $value, array $options = []) 日時選択コンポーネント
 * @method static string daterange(string $name, string $value, array $options = []) 日付範囲コンポーネント
 * @method static string timerange(string $name, string $value, array $options = []) 時間範囲コンポーネント
 * @method static string datetimerange(string $name, string $value, array $options = []) 日時範囲コンポーネント
 * @method static string fieldlist(string $name, string $value, string $title = null, string $template = null, array $options = []) フィールドリストコンポーネント
 * @method static string cxselect(string $url, array $names = [], array $values = [], array $options = []) 連動コンポーネント
 * @method static string selectRange(string $name, string $begin, string $end, string $selected = null, array $options = []) 数値範囲を選択
 * @method static string selectYear(string $name, string $begin, string $end, string $selected = null, array $options = []) 年を選択
 * @method static string selectMonth(string $name, string $selected = null, array $options = [], string $format = '%m') 月を選択
 * @method static string checkbox(string $name, string $value = '1', string $checked = null, array $options = []) 単一チェックボックス
 * @method static string checkboxs(string $name, array $list = [], string $checked = null, array $options = []) チェックボックスグループ
 * @method static string radio(string $name, string $value = null, string $checked = null, array $options = [])) 単一ラジオボタン
 * @method static string radios(string $name, array $list = [], string $checked = null, array $options = [])) ラジオボタングループ
 * @method static string image(string $name = null, string $value = null, array $inputAttr = [], array $uploadAttr = [], array $chooseAttr = [], array $previewAttr = []) 画像アップロードコンポーネント
 * @method static string images(string $name = null, string $value = null, array $inputAttr = [], array $uploadAttr = [], array $chooseAttr = [], array $previewAttr = []) 画像アップロードコンポーネント(複数画像)）
 * @method static string upload(string $name = null, string $value = null, array $inputAttr = [], array $uploadAttr = [], array $chooseAttr = [], array $previewAttr = []) ファイルアップロードコンポーネント
 * @method static string uploads(string $name = null, string $value = null, array $inputAttr = [], array $uploadAttr = [], array $chooseAttr = [], array $previewAttr = []) ファイルアップロードコンポーネント(複数ファイル)）
 * @method static string button(string $value = null, array $options = []) フォームbutton
 */
class Form
{

    /**
     * @param $name
     * @param $arguments
     * @return FormBuilder
     */
    public static function __callStatic($name, $arguments)
    {
        return call_user_func_array([FormBuilder::instance(), $name], $arguments);
    }
}

/**
 *
 * フォーム要素生成
 * @from https://github.com/illuminate/html
 * @package fast
 */
class FormBuilder
{

    /**
     * Token
     *
     * @var string
     */
    protected $csrfToken = array('name' => '__token__');

    /**
     * 作成済みのタグ名
     *
     * @var array
     */
    protected $labels = [];

    /**
     * スキップする値のフィルタイプvalue値のタイプ
     *
     * @var array
     */
    protected $skipValueTypes = array('file', 'password', 'checkbox', 'radio');

    /**
     * エスケープHTML
     * @var boolean
     */
    protected $escapeHtml = true;
    protected static $instance;

    /**
     * シングルトンを取得
     * @param array $options
     * @return static
     */
    public static function instance($options = [])
    {
        if (is_null(self::$instance)) {
            self::$instance = new static($options);
        }

        return self::$instance;
    }

    /**
     * エスケープの有無を設定
     * @param boolean $escape
     */
    public function setEscapeHtml($escape)
    {
        $this->escapeHtml = $escape;
    }

    /**
     * エスケープエンコード後の値を取得
     * @param string $value
     * @return string
     */
    public function escape($value)
    {
        if (!$this->escapeHtml) {
            return $value;
        }
        if (is_array($value)) {
            $value = json_encode($value, JSON_UNESCAPED_UNICODE);
        }
        return htmlspecialchars($value, ENT_QUOTES, 'UTF-8', false);
    }

    /**
     * 生成Token
     *
     * @param string $name
     * @param string $type
     * @return string
     */
    public function token($name = '__token__', $type = 'md5')
    {
        if (function_exists('token')) {
            return token($name, $type);
        }

        return '';
    }

    /**
     * 生成Labelラベル
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function label($name, $value = null, $options = [])
    {
        $this->labels[] = $name;

        $options = $this->attributes($options);
        $value = $this->escape($this->formatLabel($name, $value));

        return '<label for="' . $name . '"' . $options . '>' . $value . '</label>';
    }

    /**
     * Format the label value.
     *
     * @param string      $name
     * @param string|null $value
     * @return string
     */
    protected function formatLabel($name, $value)
    {
        return $value ?: ucwords(str_replace('_', ' ', $name));
    }

    /**
     * テキストボックスを生成(タイプ別)
     *
     * @param string $type
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function input($type, $name, $value = null, $options = [])
    {
        if (!isset($options['name'])) {
            $options['name'] = $name;
        }

        $id = $this->getIdAttribute($name, $options);

        if (!in_array($type, $this->skipValueTypes)) {
            $value = $this->getValueAttribute($name, $value);
            $options['class'] = isset($options['class']) ? $options['class'] . (stripos($options['class'], 'form-control') !== false ? '' : ' form-control') : 'form-control';
        }

        $merge = compact('type', 'value', 'id');
        $options = array_merge($options, $merge);

        return '<input' . $this->attributes($options) . '>';
    }

    /**
     * 通常テキストボックスを生成
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function text($name, $value = null, $options = [])
    {
        return $this->input('text', $name, $value, $options);
    }

    /**
     * パスワードテキストボックスを生成
     *
     * @param string $name
     * @param array  $options
     * @return string
     */
    public function password($name, $options = [])
    {
        return $this->input('password', $name, '', $options);
    }

    /**
     * 非表示テキストボックスを生成
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function hidden($name, $value = null, $options = [])
    {
        return $this->input('hidden', $name, $value, $options);
    }

    /**
     * 生成Emailテキストボックス
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function email($name, $value = null, $options = [])
    {
        return $this->input('email', $name, $value, $options);
    }

    /**
     * 生成URLテキストボックス
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function url($name, $value = null, $options = [])
    {
        return $this->input('url', $name, $value, $options);
    }

    /**
     * ファイルアップロードコンポーネントを生成
     *
     * @param string $name
     * @param array  $options
     * @return string
     */
    public function file($name, $options = [])
    {
        return $this->input('file', $name, null, $options);
    }

    /**
     * 複数行テキストボックスを生成
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function textarea($name, $value = null, $options = [])
    {
        if (!isset($options['name'])) {
            $options['name'] = $name;
        }

        $options = $this->setTextAreaSize($options);
        $options['id'] = $this->getIdAttribute($name, $options);
        $value = (string)$this->getValueAttribute($name, $value);

        unset($options['size']);

        $options['class'] = isset($options['class']) ? $options['class'] . (stripos($options['class'], 'form-control') !== false ? '' : ' form-control') : 'form-control';
        $options = $this->attributes($options);

        return '<textarea' . $options . '>' . $this->escape($value) . '</textarea>';
    }

    /**
     * リッチテキストエディターを生成
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function editor($name, $value = null, $options = [])
    {
        $options['class'] = isset($options['class']) ? $options['class'] . ' editor' : 'editor';
        return $this->textarea($name, $value, $options);
    }

    /**
     * デフォルトのテキストボックス行数・列数を設定
     *
     * @param array $options
     * @return array
     */
    protected function setTextAreaSize($options)
    {
        if (isset($options['size'])) {
            return $this->setQuickTextAreaSize($options);
        }

        $cols = array_get($options, 'cols', 50);
        $rows = array_get($options, 'rows', 5);

        return array_merge($options, compact('cols', 'rows'));
    }

    /**
     * に基づいてsize行数と列数を設定
     *
     * @param array $options
     * @return array
     */
    protected function setQuickTextAreaSize($options)
    {
        $segments = explode('x', $options['size']);
        return array_merge($options, array('cols' => $segments[0], 'rows' => $segments[1]));
    }

    /**
     * スライダーを生成
     *
     * @param string $name
     * @param string $min
     * @param string $max
     * @param string $step
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function slider($name, $min, $max, $step, $value = null, $options = [])
    {
        $options = array_merge($options, ['data-slider-min' => $min, 'data-slider-max' => $max, 'data-slider-step' => $step, 'data-slider-value' => $value ? $value : '']);
        $options['class'] = isset($options['class']) ? $options['class'] . (stripos($options['class'], 'form-control') !== false ? '' : ' slider form-control') : 'slider form-control';
        return $this->input('text', $name, $value, $options);
    }

    /**
     * ドロップダウンリストボックスを生成
     *
     * @param string $name
     * @param array  $list
     * @param mixed  $selected
     * @param array  $options
     * @return string
     */
    public function select($name, $list = [], $selected = null, $options = [])
    {
        $selected = $this->getValueAttribute($name, $selected);

        $options['id'] = $this->getIdAttribute($name, $options);

        if (!isset($options['name'])) {
            $options['name'] = $name;
        }

        $html = [];
        foreach ($list as $value => $display) {
            $html[] = $this->getSelectOption($display, $value, $selected);
        }
        $options['class'] = isset($options['class']) ? $options['class'] . (stripos($options['class'], 'form-control') !== false ? '' : ' form-control') : 'form-control';

        $options = $this->attributes($options);
        $list = implode('', $html);

        return "<select{$options}>{$list}</select>";
    }

    /**
     * ドロップダウンリスト(複数選択)
     *
     * @param string $name
     * @param array  $list
     * @param mixed  $selected
     * @param array  $options
     * @return string
     */
    public function selects($name, $list = [], $selected = null, $options = [])
    {
        $options[] = 'multiple';
        return $this->select($name, $list, $selected, $options);
    }

    /**
     * ドロップダウンリスト(フレンドリー)
     *
     * @param string $name
     * @param array  $list
     * @param mixed  $selected
     * @param array  $options
     * @return string
     */
    public function selectpicker($name, $list = [], $selected = null, $options = [])
    {
        $options['class'] = isset($options['class']) ? $options['class'] . ' selectpicker' : 'selectpicker';
        return $this->select($name, $list, $selected, $options);
    }

    /**
     * ドロップダウンリスト(フレンドリー)(複数選択)
     *
     * @param string $name
     * @param array  $list
     * @param mixed  $selected
     * @param array  $options
     * @return string
     */
    public function selectpickers($name, $list = [], $selected = null, $options = [])
    {
        $options[] = 'multiple';
        return $this->selectpicker($name, $list, $selected, $options);
    }

    /**
     * 動的ドロップダウンリストを生成
     *
     * @param string $name       名称
     * @param mixed  $value
     * @param string $url        データソースURL
     * @param string $field      表示フィールド名,デフォルトはname
     * @param string $primaryKey 主キー,データベースに保存される値,デフォルトはid
     * @param array  $options
     * @return string
     */
    public function selectpage($name, $value, $url, $field = null, $primaryKey = null, $options = [])
    {
        $options = array_merge($options, ['data-source' => $url, 'data-field' => $field ? $field : 'name', 'data-primary-key' => $primaryKey ? $primaryKey : 'id']);
        $options['class'] = isset($options['class']) ? $options['class'] . ' selectpage' : 'selectpage';
        return $this->text($name, $value, $options);
    }


    /**
     * 動的ドロップダウンリストを生成(複数選択)
     *
     * @param string $name       名称
     * @param mixed  $value
     * @param string $url        データソースURL
     * @param string $field      表示フィールド名,デフォルトはname
     * @param string $primaryKey 主キー,データベースに保存される値,デフォルトはid
     * @param array  $options
     * @return string
     */
    public function selectpages($name, $value, $url, $field = null, $primaryKey = null, $options = [])
    {
        $options['data-multiple'] = "true";
        return $this->selectpage($name, $value, $url, $field, $primaryKey, $options);
    }

    /**
     * 都市選択ボックスを生成
     *
     * @param string $name
     * @param mixed  $value
     * @param array  $options
     * @return string
     */
    public function citypicker($name, $value, $options = [])
    {
        $options['data-toggle'] = 'city-picker';
        return "<div class='control-relative'>" . $this->text($name, $value, $options) . "</div>";
    }

    /**
     * 生成switchコンポーネント
     *
     * @param string $name
     * @param mixed  $value
     * @param array  $options
     * @return string
     */
    public function switcher($name, $value, $options = [])
    {
        $domname = str_replace(['[', ']', '.'], '', $name);
        $btn = $this->hidden($name, $value, ['id' => "c-{$domname}"]);
        $yes = 1;
        $no = 0;
        if (isset($options['yes']) && isset($options['no'])) {
            $yes = $options['yes'];
            $no = $options['no'];
        }
        $selected = $no == $value ? "fa-flip-horizontal text-gray" : "";
        $disabled = (isset($options['disabled']) && $options['disabled']) || in_array('disabled', $options) ? "disabled" : '';
        $color = isset($options['color']) ? $options['color'] : 'success';
        unset($options['yes'], $options['no'], $options['color'], $options['disabled']);
        $attr = $this->attributes($options);
        $html = <<<EOD
{$btn}
<a href="javascript:;" data-toggle="switcher" class="btn-switcher {$disabled}" data-input-id="c-{$domname}" data-yes="{$yes}" data-no="{$no}" {$attr}><i class="fa fa-toggle-on text-{$color} {$selected} fa-2x"></i></a>
EOD;
        return $html;
    }

    /**
     * 日付ピッカー
     * @param string $name
     * @param mixed  $value
     * @param array  $options
     * @return string
     */
    public function datepicker($name, $value, $options = [])
    {
        $defaults = [
            'data-date-format' => "YYYY-MM-DD",
        ];
        $options = array_merge($defaults, $options);
        $value = is_numeric($value) ? date("Y-m-d", $value) : $value;
        return $this->datetimepicker($name, $value, $options);
    }

    /**
     * 時間ピッカー
     *
     * @param string $name
     * @param mixed  $value
     * @param array  $options
     * @return string
     */
    public function timepicker($name, $value, $options = [])
    {
        $defaults = [
            'data-date-format' => "HH:mm:ss",
        ];
        $options = array_merge($defaults, $options);
        $value = is_numeric($value) ? date("H:i:s", $value) : $value;
        return $this->datetimepicker($name, $value, $options);
    }

    /**
     * 日時ピッカー
     *
     * @param string $name
     * @param mixed  $value
     * @param array  $options
     * @return string
     */
    public function datetimepicker($name, $value, $options = [])
    {
        $defaults = [
            'data-date-format' => "YYYY-MM-DD HH:mm:ss",
            'data-use-current' => "true",
        ];
        $value = is_numeric($value) ? date("Y-m-d H:i:s", $value) : $value;
        $options = array_merge($defaults, $options);
        $options['class'] = isset($options['class']) ? $options['class'] . ' datetimepicker' : 'datetimepicker';
        return $this->text($name, $value, $options);
    }

    /**
     * 日付範囲
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function daterange($name, $value, $options = [])
    {
        $defaults = [
            'data-locale' => [
                'format' => 'YYYY-MM-DD'
            ]
        ];
        $options = array_merge($defaults, $options);
        return $this->datetimerange($name, $value, $options);
    }

    /**
     * 時間範囲
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function timerange($name, $value, $options = [])
    {
        $defaults = [
            'data-locale'                  => [
                'format' => 'HH:mm:ss'
            ],
            'data-ranges'                  => [],
            'data-show-custom-range-label' => "false",
            'data-time-picker'             => "true",
        ];
        $options = array_merge($defaults, $options);
        return $this->datetimerange($name, $value, $options);
    }

    /**
     * 日時範囲
     *
     * @param string $name
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function datetimerange($name, $value, $options = [])
    {
        $defaults = [
            'data-locale' => [
                'format' => 'YYYY-MM-DD HH:mm:ss'
            ]
        ];
        $options = array_merge($defaults, $options);
        $options['class'] = isset($options['class']) ? $options['class'] . ' datetimerange' : 'datetimerange';
        return $this->text($name, $value, $options);
    }

    /**
     * フィールドリストコンポーネントを生成
     *
     * @param string $name
     * @param mixed  $value
     * @param array  $title
     * @param string $template
     * @param array  $options
     * @return string
     */
    public function fieldlist($name, $value, $title = null, $template = null, $options = [])
    {
        $append = __('Append');
        $template = $template ? 'data-template="' . $template . '"' : '';
        $attributes = $this->attributes($options);
        if (is_null($title)) {
            $title = [__('Key'), __('Value')];
        }
        $ins = implode("\n", array_map(function ($value) {
            return "<ins>{$value}</ins>";
        }, $title));
        $value = is_array($value) ? json_encode($value) : $value;
        $html = <<<EOD
<dl class="fieldlist" data-name="{$name}" {$template} {$attributes}>
    <dd>
        {$ins}
    </dd>
    <dd><a href="javascript:;" class="btn btn-sm btn-success btn-append"><i class="fa fa-plus"></i> {$append}</a></dd>
    <textarea name="{$name}" class="form-control hide" cols="30" rows="5">{$value}</textarea>
</dl>
EOD;
        return $html;
    }

    /**
     * 連動プルダウンリストを生成
     *
     * @param string $url     連動してデータソースを取得するURLアドレス
     * @param array  $names   連動フィールド名
     * @param array  $values  連動フィールドのデフォルト選択値
     * @param array  $options 拡張属性
     * @return string
     */
    public function cxselect($url, $names = [], $values = [], $options = [])
    {
        $classes = [];
        $cxselect = [];
        $attributes = $this->attributes($options);
        foreach ($names as $index => $value) {
            $level = $index + 1;
            $class = "cxselect-{$level}";
            $classes[] = $class;
            $selectValue = isset($values[$value]) ? $values[$value] : (isset($values[$index]) ? $values[$index] : '');

            $cxselect[] = <<<EOD
<select class="{$class} form-control" name="{$value}" data-value="{$selectValue}" data-url="{$url}?level={$level}&name={$value}" {$attributes}></select>
EOD;
        }
        $cxselect = implode("\n", $cxselect);
        $selects = implode(',', $classes);
        $html = <<<EOD
<div class="form-inline" data-toggle="cxselect" data-selects="{$selects}">
{$cxselect}
</div>
EOD;
        return $html;
    }

    /**
     * プルダウンリストによる範囲選択コンポーネントを作成
     *
     * @param string $name
     * @param string $begin
     * @param string $end
     * @param string $selected
     * @param array  $options
     * @return string
     */
    public function selectRange($name, $begin, $end, $selected = null, $options = [])
    {
        $range = array_combine($range = range($begin, $end), $range);
        return $this->select($name, $range, $selected, $options);
    }

    /**
     * 年選択コンポーネントを生成
     *
     * @param string $name
     * @param string $begin
     * @param string $end
     * @param string $selected
     * @param array  $options
     * @return string
     */
    public function selectYear($name, $begin, $end, $selected, $options)
    {
        return call_user_func_array(array($this, 'selectRange'), func_get_args());
    }

    /**
     * 月選択コンポーネントを生成
     *
     * @param string $name
     * @param string $selected
     * @param array  $options
     * @param string $format
     * @return string
     */
    public function selectMonth($name, $selected = null, $options = [], $format = '%m')
    {
        $months = [];

        foreach (range(1, 12) as $month) {
            $months[$month] = strftime($format, mktime(0, 0, 0, $month, 1));
        }

        return $this->select($name, $months, $selected, $options);
    }

    /**
     * 渡された値に基づいて生成option
     *
     * @param string $display
     * @param string $value
     * @param string $selected
     * @return string
     */
    public function getSelectOption($display, $value, $selected)
    {
        if (is_array($display)) {
            return $this->optionGroup($display, $value, $selected);
        }

        return $this->option($display, $value, $selected);
    }

    /**
     * 生成optionGroup
     *
     * @param array  $list
     * @param string $label
     * @param string $selected
     * @return string
     */
    protected function optionGroup($list, $label, $selected)
    {
        $html = [];

        foreach ($list as $value => $display) {
            $html[] = $this->option($display, $value, $selected);
        }

        return '<optgroup label="' . $this->escape($label) . '">' . implode('', $html) . '</optgroup>';
    }

    /**
     * 生成optionオプション
     *
     * @param string $display
     * @param string $value
     * @param string $selected
     * @return string
     */
    protected function option($display, $value, $selected)
    {
        $selected = $this->getSelectedValue($value, $selected);

        $options = array('value' => $this->escape($value), 'selected' => $selected);

        return '<option' . $this->attributes($options) . '>' . $this->escape($display) . '</option>';
    }

    /**
     * チェックvalue選択されているかどうか
     *
     * @param string $value
     * @param string $selected
     * @return string
     */
    protected function getSelectedValue($value, $selected)
    {
        if (is_array($selected)) {
            return in_array($value, $selected) ? 'selected' : null;
        }

        return ((string)$value == (string)$selected) ? 'selected' : null;
    }

    /**
     * チェックボックスを生成
     *
     * @param string $name
     * @param mixed  $value
     * @param bool   $checked
     * @param array  $options
     * @return string
     */
    public function checkbox($name, $value = 1, $checked = null, $options = [])
    {
        if ($checked) {
            $options['checked'] = 'checked';
        }

        return $this->input('checkbox', $name, $value, $options);
    }

    /**
     * 一組のフィルターボックスを生成
     *
     * @param string $name
     * @param array  $list
     * @param mixed  $checked
     * @param array  $options
     * @return string
     */
    public function checkboxs($name, $list, $checked, $options = [])
    {
        $html = [];
        $checked = is_null($checked) ? [] : $checked;
        $checked = is_array($checked) ? $checked : explode(',', $checked);
        foreach ($list as $k => $v) {
            $options['id'] = "{$name}-{$k}";
            $html[] = sprintf(Form::label("{$name}-{$k}", "%s " . str_replace('%', '%%', $v)), Form::checkbox("{$name}[{$k}]", $k, in_array($k, $checked), $options));
        }
        return '<div class="checkbox">' . implode(' ', $html) . '</div>';
    }

    /**
     * ラジオボタンを生成
     *
     * @param string $name
     * @param mixed  $value
     * @param bool   $checked
     * @param array  $options
     * @return string
     */
    public function radio($name, $value = null, $checked = null, $options = [])
    {
        if (is_null($value)) {
            $value = $name;
        }

        if ($checked) {
            $options['checked'] = 'checked';
        }

        return $this->input('radio', $name, $value, $options);
    }

    /**
     * 一組のラジオボタンを生成
     *
     * @param string $name
     * @param array  $list
     * @param mixed  $checked
     * @param array  $options
     * @return string
     */
    public function radios($name, $list, $checked = null, $options = [])
    {
        $html = [];
        $checked = is_null($checked) ? key($list) : $checked;
        $checked = is_array($checked) ? $checked : explode(',', $checked);
        foreach ($list as $k => $v) {
            $options['id'] = "{$name}-{$k}";
            $html[] = sprintf(Form::label("{$name}-{$k}", "%s " . str_replace('%', '%%', $v)), Form::radio($name, $k, in_array($k, $checked), $options));
        }
        return '<div class="radio">' . implode(' ', $html) . '</div>';
    }

    /**
     * 画像アップロードコンポーネントを生成(単一画像)
     *
     * @param string $name
     * @param string $value
     * @param array  $inputAttr
     * @param array  $uploadAttr
     * @param array  $chooseAttr
     * @param array  $previewAttr
     * @return string
     */
    public function image($name = null, $value = null, $inputAttr = [], $uploadAttr = [], $chooseAttr = [], $previewAttr = [])
    {
        $default = [
            'data-mimetype' => 'image/gif,image/jpeg,image/png,image/jpg,image/bmp'
        ];
        $uploadAttr = is_array($uploadAttr) ? array_merge($default, $uploadAttr) : $uploadAttr;
        $chooseAttr = is_array($chooseAttr) ? array_merge($default, $chooseAttr) : $chooseAttr;
        return $this->uploader($name, $value, $inputAttr, $uploadAttr, $chooseAttr, $previewAttr);
    }

    /**
     * 画像アップロードコンポーネントを生成(複数画像)
     *
     * @param string $name
     * @param string $value
     * @param array  $inputAttr
     * @param array  $uploadAttr
     * @param array  $chooseAttr
     * @param array  $previewAttr
     * @return string
     */
    public function images($name = null, $value = null, $inputAttr = [], $uploadAttr = [], $chooseAttr = [], $previewAttr = [])
    {
        $default = [
            'data-multiple' => 'true',
            'data-mimetype' => 'image/gif,image/jpeg,image/png,image/jpg,image/bmp'
        ];
        $uploadAttr = is_array($uploadAttr) ? array_merge($default, $uploadAttr) : $uploadAttr;
        $chooseAttr = is_array($chooseAttr) ? array_merge($default, $chooseAttr) : $chooseAttr;
        return $this->uploader($name, $value, $inputAttr, $uploadAttr, $chooseAttr, $previewAttr);
    }

    /**
     * ファイルアップロードコンポーネントを生成(単一ファイル)
     *
     * @param string $name
     * @param string $value
     * @param array  $inputAttr
     * @param array  $uploadAttr
     * @param array  $chooseAttr
     * @param array  $previewAttr
     * @return string
     */
    public function upload($name = null, $value = null, $inputAttr = [], $uploadAttr = [], $chooseAttr = [], $previewAttr = [])
    {
        return $this->uploader($name, $value, $inputAttr, $uploadAttr, $chooseAttr, $previewAttr);
    }

    /**
     * ファイルアップロードコンポーネントを生成(複数ファイル)
     *
     * @param string $name
     * @param string $value
     * @param array  $inputAttr
     * @param array  $uploadAttr
     * @param array  $chooseAttr
     * @param array  $previewAttr
     * @return string
     */
    public function uploads($name = null, $value = null, $inputAttr = [], $uploadAttr = [], $chooseAttr = [], $previewAttr = [])
    {
        $default = [
            'data-multiple' => 'true',
        ];
        $uploadAttr = is_array($uploadAttr) ? array_merge($default, $uploadAttr) : $uploadAttr;
        $chooseAttr = is_array($chooseAttr) ? array_merge($default, $chooseAttr) : $chooseAttr;
        return $this->uploader($name, $value, $inputAttr, $uploadAttr, $chooseAttr, $previewAttr);
    }

    protected function uploader($name = null, $value = null, $inputAttr = [], $uploadAttr = [], $chooseAttr = [], $previewAttr = [])
    {
        $domname = str_replace(['[', ']', '.'], '', $name);
        $options = [
            'id'            => "faupload-{$domname}",
            'class'         => "btn btn-danger faupload",
            'data-input-id' => "c-{$domname}",
        ];
        $upload = $uploadAttr === false ? false : true;
        $choose = $chooseAttr === false ? false : true;
        $preview = $previewAttr === false ? false : true;
        if ($preview) {
            $options['data-preview-id'] = "p-{$domname}";
        }
        $uploadBtn = $upload ? $this->button('<i class="fa fa-upload"></i> ' . __('Upload'), array_merge($options, $uploadAttr)) : '';
        $options = [
            'id'            => "fachoose-{$domname}",
            'class'         => "btn btn-danger fachoose",
            'data-input-id' => "c-{$domname}",
        ];
        if ($preview) {
            $options['data-preview-id'] = "p-{$domname}";
        }
        $chooseBtn = $choose ? $this->button('<i class="fa fa-list"></i> ' . __('Choose'), array_merge($options, $chooseAttr)) : '';
        $previewAttrHtml = $this->attributes($previewAttr);
        $previewArea = $preview ? '<ul class="row list-inline faupload-preview" id="p-' . $domname . '" ' . $previewAttrHtml . '></ul>' : '';
        $input = $this->text($name, $value, array_merge(['size' => 50, 'id' => "c-{$domname}"], $inputAttr));
        $html = <<<EOD
<div class="input-group">
                {$input}
                <div class="input-group-addon no-border no-padding">
                    <span>{$uploadBtn}</span>                  
                    <span>{$chooseBtn}</span>
                </div>
                <span class="msg-box n-right" for="c-{$domname}"></span>
            </div>
            {$previewArea}
EOD;
        return $html;
    }

    /**
     * ボタンを1つ生成
     *
     * @param string $value
     * @param array  $options
     * @return string
     */
    public function button($value = null, $options = [])
    {
        if (!array_key_exists('type', $options)) {
            $options['type'] = 'button';
        }

        return '<button' . $this->attributes($options) . '>' . $value . '</button>';
    }

    /**
     * 取得ID属性値
     *
     * @param string $name
     * @param array  $attributes
     * @return string
     */
    public function getIdAttribute($name, $attributes)
    {
        if (array_key_exists('id', $attributes)) {
            return $attributes['id'];
        }

        if (in_array($name, $this->labels)) {
            return $name;
        }
    }

    /**
     * 取得Value属性値
     *
     * @param string $name
     * @param string $value
     * @return string
     */
    public function getValueAttribute($name, $value = null)
    {
        if (is_null($name)) {
            return $value;
        }

        if (!is_null($value)) {
            return $value;
        }
    }

    /**
     * 配列をHTML属性文字列に変換。
     *
     * @param array $attributes
     * @return string
     */
    public function attributes($attributes)
    {
        $html = [];
        // 仮に我々のkeys と value が同じだとすると,
        // 例として挙げるとHTML“required”属性として言うと,と仮定する['required']配列,
        // はすでに required="required" 連結される,数値keysで連結するのではなく
        foreach ((array)$attributes as $key => $value) {
            $element = $this->attributeElement($key, $value);
            if (!is_null($element)) {
                $html[] = $element;
            }
        }
        return count($html) > 0 ? ' ' . implode(' ', $html) : '';
    }

    /**
     * 1つの属性に連結する。
     *
     * @param string $key
     * @param string $value
     * @return string
     */
    protected function attributeElement($key, $value)
    {
        if (is_numeric($key)) {
            $key = $value;
        }
        if (!is_null($value)) {
            if (is_array($value) || stripos($value, '"') !== false) {
                $value = is_array($value) ? json_encode($value, JSON_UNESCAPED_UNICODE) : $value;
                return $key . "='" . $value . "'";
            } else {
                return $key . '="' . $value . '"';
            }
        }
    }
}

class Arr
{

    /**
     * Determine whether the given value is array accessible.
     *
     * @param mixed $value
     * @return bool
     */
    public static function accessible($value)
    {
        return is_array($value) || $value instanceof ArrayAccess;
    }

    /**
     * Determine if the given key exists in the provided array.
     *
     * @param \ArrayAccess|array $array
     * @param string|int         $key
     * @return bool
     */
    public static function exists($array, $key)
    {
        if ($array instanceof ArrayAccess) {
            return $array->offsetExists($key);
        }
        return array_key_exists($key, $array);
    }

    /**
     * Get an item from an array using "dot" notation.
     *
     * @param \ArrayAccess|array $array
     * @param string             $key
     * @param mixed              $default
     * @return mixed
     */
    public static function get($array, $key, $default = null)
    {
        if (!static::accessible($array)) {
            return $default;
        }
        if (is_null($key)) {
            return $array;
        }
        if (static::exists($array, $key)) {
            return $array[$key];
        }
        foreach (explode('.', $key) as $segment) {
            if (static::accessible($array) && static::exists($array, $segment)) {
                $array = $array[$segment];
            } else {
                return $default;
            }
        }
        return $array;
    }

    /**
     * Get all of the given array except for a specified array of items.
     *
     * @param array        $array
     * @param array|string $keys
     * @return array
     */
    public static function except($array, $keys)
    {
        static::forget($array, $keys);
        return $array;
    }

    /**
     * Remove one or many array items from a given array using "dot" notation.
     *
     * @param array        $array
     * @param array|string $keys
     * @return void
     */
    public static function forget(&$array, $keys)
    {
        $original = &$array;
        $keys = (array)$keys;
        if (count($keys) === 0) {
            return;
        }
        foreach ($keys as $key) {
            // if the exact key exists in the top-level, remove it
            if (static::exists($array, $key)) {
                unset($array[$key]);
                continue;
            }
            $parts = explode('.', $key);
            // clean up before each pass
            $array = &$original;
            while (count($parts) > 1) {
                $part = array_shift($parts);
                if (isset($array[$part]) && is_array($array[$part])) {
                    $array = &$array[$part];
                } else {
                    continue 2;
                }
            }
            unset($array[array_shift($parts)]);
        }
    }
}

if (!function_exists('array_get')) {

    /**
     * Get an item from an array using "dot" notation.
     *
     * @param \ArrayAccess|array $array
     * @param string             $key
     * @param mixed              $default
     * @return mixed
     */
    function array_get($array, $key, $default = null)
    {
        return Arr::get($array, $key, $default);
    }
}
if (!function_exists('e')) {

    /**
     * Escape HTML special characters in a string.
     *
     *
     * @return string
     */
    function e($value)
    {
        if (is_array($value)) {
            $value = json_encode($value, JSON_UNESCAPED_UNICODE);
        }
        return htmlspecialchars($value, ENT_QUOTES, 'UTF-8', false);
    }
}
if (!function_exists('array_except')) {

    /**
     * Get all of the given array except for a specified array of items.
     *
     * @param array        $array
     * @param array|string $keys
     * @return array
     */
    function array_except($array, $keys)
    {
        return Arr::except($array, $keys);
    }
}
