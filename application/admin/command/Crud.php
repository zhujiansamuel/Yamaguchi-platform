<?php

namespace app\admin\command;

use fast\Form;
use think\Config;
use think\console\Command;
use think\console\Input;
use think\console\input\Option;
use think\console\Output;
use think\Db;
use think\Exception;
use think\exception\ErrorException;
use think\exception\PDOException;
use think\Lang;
use think\Loader;

class Crud extends Command
{
    protected $stubList = [];

    protected $internalKeywords = [
        'abstract',
        'and',
        'array',
        'as',
        'break',
        'callable',
        'case',
        'catch',
        'class',
        'clone',
        'const',
        'continue',
        'declare',
        'default',
        'die',
        'do',
        'echo',
        'else',
        'elseif',
        'empty',
        'enddeclare',
        'endfor',
        'endforeach',
        'endif',
        'endswitch',
        'endwhile',
        'eval',
        'exit',
        'extends',
        'final',
        'for',
        'foreach',
        'function',
        'global',
        'goto',
        'if',
        'implements',
        'include',
        'include_once',
        'instanceof',
        'insteadof',
        'interface',
        'isset',
        'list',
        'namespace',
        'new',
        'or',
        'print',
        'private',
        'protected',
        'public',
        'require',
        'require_once',
        'return',
        'static',
        'switch',
        'throw',
        'trait',
        'try',
        'unset',
        'use',
        'var',
        'while',
        'xor'
    ];

    /**
     * 保護されたシステムテーブル, crudは有効になりません
     */
    protected $systemTables = [
        'admin',
        'admin_log',
        'auth_group',
        'auth_group_access',
        'auth_rule',
        'attachment',
        'config',
        'category',
        'ems',
        'sms',
        'user',
        'user_group',
        'user_rule',
        'user_score_log',
        'user_token',
    ];

    /**
     * Selectpage検索フィールドの関連付け
     */
    protected $fieldSelectpageMap = [
        'nickname' => ['user_id', 'user_ids', 'admin_id', 'admin_ids']
    ];

    /**
     * Enumタイプをラジオボタンと判定する末尾文字,デフォルトでは単一選択ドロップダウンとして認識されます
     */
    protected $enumRadioSuffix = ['data', 'state', 'status'];

    /**
     * Setタイプをチェックボックスと判定する末尾文字,デフォルトでは複数選択ドロップダウンとして認識されます
     */
    protected $setCheckboxSuffix = ['data', 'state', 'status'];

    /**
     * Intタイプを日時と判定する末尾文字,デフォルトでは日付テキストボックスとして認識されます
     */
    protected $intDateSuffix = ['time'];

    /**
     * スイッチ用サフィックス
     */
    protected $switchSuffix = ['switch'];

    /**
     * リッチテキスト接尾辞
     */
    protected $editorSuffix = ['content'];

    /**
     * 都市接尾辞
     */
    protected $citySuffix = ['city'];

    /**
     * 時間範囲接尾辞
     */
    protected $rangeSuffix = ['range'];

    /**
     * JSONサフィックス
     */
    protected $jsonSuffix = ['json', 'array'];

    /**
     * タグ接尾辞
     */
    protected $tagSuffix = ['tag', 'tags'];

    /**
     * Selectpage対応する接尾辞
     */
    protected $selectpageSuffix = ['_id', '_ids'];

    /**
     * Selectpage複数選択用の対応接尾辞
     */
    protected $selectpagesSuffix = ['_ids'];

    /**
     * 指定文字で終わるフィールドのフォーマット関数
     */
    protected $fieldFormatterSuffix = [
        'status' => ['type' => ['varchar', 'enum'], 'name' => 'status'],
        'icon'   => 'icon',
        'flag'   => 'flag',
        'url'    => 'url',
        'image'  => 'image',
        'images' => 'images',
        'file'   => 'file',
        'files'  => 'files',
        'avatar' => 'image',
        'switch' => 'toggle',
        'tag'    => 'flag',
        'tags'   => 'flag',
        'time'   => ['type' => ['int', 'bigint', 'timestamp'], 'name' => 'datetime'],
    ];

    /**
     * 画像フィールドとして識別
     */
    protected $imageField = ['image', 'images', 'avatar', 'avatars'];

    /**
     * ファイルフィールドとして識別
     */
    protected $fileField = ['file', 'files'];

    /**
     * 予約フィールド
     */
    protected $reservedField = ['admin_id'];

    /**
     * 除外フィールド
     */
    protected $ignoreFields = [];

    /**
     * ソートフィールド
     */
    protected $sortField = 'weigh';

    /**
     * フィルターフィールド
     * @var string
     */
    protected $headingFilterField = 'status';

    /**
     * 作成時刻フィールド
     * @var string
     */
    protected $createTimeField = 'createtime';

    /**
     * 更新時間フィールド
     * @var string
     */
    protected $updateTimeField = 'updatetime';

    /**
     * ソフト削除時刻フィールド
     * @var string
     */
    protected $deleteTimeField = 'deletetime';

    /**
     * エディターのClass
     */
    protected $editorClass = 'editor';

    /**
     * langListのkey最長バイト数
     */
    protected $fieldMaxLen = 0;

    protected function configure()
    {
        $this
            ->setName('crud')
            ->addOption('table', 't', Option::VALUE_REQUIRED, 'table name without prefix', null)
            ->addOption('controller', 'c', Option::VALUE_OPTIONAL, 'controller name', null)
            ->addOption('model', 'm', Option::VALUE_OPTIONAL, 'model name', null)
            ->addOption('fields', 'i', Option::VALUE_OPTIONAL, 'model visible fields', null)
            ->addOption('force', 'f', Option::VALUE_OPTIONAL, 'force override or force delete,without tips', null)
            ->addOption('local', 'l', Option::VALUE_OPTIONAL, 'local model', 1)
            ->addOption('import', 'a', Option::VALUE_OPTIONAL, 'enable import function', 0)
            ->addOption('relation', 'r', Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'relation table name without prefix', null)
            ->addOption('relationmodel', 'e', Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'relation model name', null)
            ->addOption('relationforeignkey', 'k', Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'relation foreign key', null)
            ->addOption('relationprimarykey', 'p', Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'relation primary key', null)
            ->addOption('relationfields', 's', Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'relation table fields', null)
            ->addOption('relationmode', 'o', Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'relation table mode,hasone/belongsto/hasmany', null)
            ->addOption('relationcontroller', 'w', Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'relation table controller,only work at hasmany mode', null)
            ->addOption('delete', 'd', Option::VALUE_OPTIONAL, 'delete all files generated by CRUD', null)
            ->addOption('menu', 'u', Option::VALUE_OPTIONAL, 'create menu when CRUD completed', null)
            ->addOption('setcheckboxsuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate checkbox component with suffix', null)
            ->addOption('enumradiosuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate radio component with suffix', null)
            ->addOption('imagefield', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate image component with suffix', null)
            ->addOption('filefield', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate file component with suffix', null)
            ->addOption('intdatesuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate date component with suffix', null)
            ->addOption('switchsuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate switch component with suffix', null)
            ->addOption('citysuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate citypicker component with suffix', null)
            ->addOption('jsonsuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate fieldlist component with suffix', null)
            ->addOption('tagsuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate tag component with suffix', null)
            ->addOption('editorsuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate editor component with suffix', null)
            ->addOption('selectpagesuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate selectpage component with suffix', null)
            ->addOption('selectpagessuffix', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'automatically generate multiple selectpage component with suffix', null)
            ->addOption('ignorefields', null, Option::VALUE_OPTIONAL | Option::VALUE_IS_ARRAY, 'ignore fields', null)
            ->addOption('sortfield', null, Option::VALUE_OPTIONAL, 'sort field', null)
            ->addOption('headingfilterfield', null, Option::VALUE_OPTIONAL, 'heading filter field', null)
            ->addOption('fixedcolumns', null, Option::VALUE_OPTIONAL, 'fixed columns', null)
            ->addOption('editorclass', null, Option::VALUE_OPTIONAL, 'automatically generate editor class', null)
            ->addOption('db', null, Option::VALUE_OPTIONAL, 'database config name', 'database')
            ->setDescription('Build CRUD controller and model from table');
    }

    protected function execute(Input $input, Output $output)
    {
        $adminPath = dirname(__DIR__) . DS;
        //データベース
        $db = $input->getOption('db');
        //テーブル名
        $table = $input->getOption('table') ?: '';
        //カスタムコントローラー
        $controller = $input->getOption('controller');
        //カスタムモデル
        $model = $input->getOption('model');
        $model = $model ? $model : $controller;
        //バリデーションクラス
        $validate = $model;
        //カスタム表示フィールド
        $fields = $input->getOption('fields');
        //強制上書き
        $force = $input->getOption('force');
        //是否ための本地model,ための0时表示ための全局model配置するmodelに配置app/common/model中
        $local = $input->getOption('local');
        //インポート機能を有効にするかどうか
        $import = $input->getOption('import');

        if (!$table) {
            throw new Exception('table name can\'t empty');
        }


        //メニューを生成するかどうか
        $menu = $input->getOption("menu");
        //関連テーブル
        $relation = $input->getOption('relation');
        //カスタム関連テーブルモデル
        $relationModels = $input->getOption('relationmodel');
        //モード
        $relationMode = $mode = $input->getOption('relationmode');
        //外部キー
        $relationForeignKey = $input->getOption('relationforeignkey');
        //主キー
        $relationPrimaryKey = $input->getOption('relationprimarykey');
        //関連テーブル表示フィールド
        $relationFields = $input->getOption('relationfields');
        //関連テーブル表示フィールド
        $relationController = $input->getOption('relationcontroller');
        //チェックボックス接尾辞
        $setcheckboxsuffix = $input->getOption('setcheckboxsuffix');
        //ラジオボタン接尾辞
        $enumradiosuffix = $input->getOption('enumradiosuffix');
        //画像接尾辞
        $imagefield = $input->getOption('imagefield');
        //ファイル接尾辞
        $filefield = $input->getOption('filefield');
        //タグ接尾辞
        $tagsuffix = $input->getOption('tagsuffix');
        //日付接尾辞
        $intdatesuffix = $input->getOption('intdatesuffix');
        //スイッチ用サフィックス
        $switchsuffix = $input->getOption('switchsuffix');
        //リッチテキストエディター
        $editorsuffix = $input->getOption('editorsuffix');
        //都市接尾辞
        $citysuffix = $input->getOption('citysuffix');
        //JSON設定接尾辞
        $jsonsuffix = $input->getOption('jsonsuffix');
        //selectpageサフィックス
        $selectpagesuffix = $input->getOption('selectpagesuffix');
        //selectpage複数選択接尾辞
        $selectpagessuffix = $input->getOption('selectpagessuffix');
        //除外フィールド
        $ignoreFields = $input->getOption('ignorefields');
        //ソートフィールド
        $sortfield = $input->getOption('sortfield');
        //上部フィルター用フィールド
        $headingfilterfield = $input->getOption('headingfilterfield');
        //固定列数
        $fixedcolumns = $input->getOption('fixedcolumns');
        //エディターClass
        $editorclass = $input->getOption('editorclass');
        if ($setcheckboxsuffix) {
            $this->setCheckboxSuffix = $setcheckboxsuffix;
        }
        if ($enumradiosuffix) {
            $this->enumRadioSuffix = $enumradiosuffix;
        }
        if ($imagefield) {
            $this->imageField = $imagefield;
        }
        if ($filefield) {
            $this->fileField = $filefield;
        }
        if ($tagsuffix) {
            $this->tagSuffix = $tagsuffix;
        }
        if ($intdatesuffix) {
            $this->intDateSuffix = $intdatesuffix;
        }
        if ($switchsuffix) {
            $this->switchSuffix = $switchsuffix;
        }
        if ($editorsuffix) {
            $this->editorSuffix = $editorsuffix;
        }
        if ($citysuffix) {
            $this->citySuffix = $citysuffix;
        }
        if ($jsonsuffix) {
            $this->jsonSuffix = $jsonsuffix;
        }
        if ($selectpagesuffix) {
            $this->selectpageSuffix = $selectpagesuffix;
        }
        if ($selectpagessuffix) {
            $this->selectpagesSuffix = $selectpagessuffix;
        }
        if ($ignoreFields) {
            $this->ignoreFields = $ignoreFields;
        }
        if ($editorclass) {
            $this->editorClass = $editorclass;
        }
        if ($sortfield) {
            $this->sortField = $sortfield;
        }
        if ($headingfilterfield) {
            $this->headingFilterField = $headingfilterfield;
        }

        $this->reservedField = array_merge($this->reservedField, [$this->createTimeField, $this->updateTimeField, $this->deleteTimeField]);

        $dbconnect = Db::connect($db);
        $dbname = Config::get($db . '.database');
        $prefix = Config::get($db . '.prefix');

        //システムテーブルは生成できません，バックエンドの乱れを防止するため
        if (in_array(str_replace($prefix, "", $table), $this->systemTables)) {
            throw new Exception('system table can\'t be crud');
        }

        //モジュール
        $moduleName = 'admin';
        $modelModuleName = $local ? $moduleName : 'common';
        $validateModuleName = $local ? $moduleName : 'common';

        //メインテーブルを確認
        $modelName = $table = stripos($table, $prefix) === 0 ? substr($table, strlen($prefix)) : $table;
        $modelTableType = 'table';
        $modelTableTypeName = $modelTableName = $modelName;
        $modelTableInfo = null;
        if (!$input->getOption('delete')) {
            $modelTableInfo = $dbconnect->query("SHOW TABLE STATUS LIKE '{$modelTableName}'", [], true);
            if (!$modelTableInfo) {
                $modelTableType = 'name';
                $modelTableName = $prefix . $modelName;
                $modelTableInfo = $dbconnect->query("SHOW TABLE STATUS LIKE '{$modelTableName}'", [], true);
                if (!$modelTableInfo) {
                    throw new Exception("table not found");
                }
            }
            $modelTableInfo = $modelTableInfo[0];
        }

        $relations = [];
        //関連テーブルを確認
        if ($relation) {
            $relationArr = $relation;
            $relations = [];

            foreach ($relationArr as $index => $relationTable) {
                $relationName = stripos($relationTable, $prefix) === 0 ? substr($relationTable, strlen($prefix)) : $relationTable;
                $relationTableType = 'table';
                $relationTableTypeName = $relationTableName = $relationName;
                $relationTableInfo = $dbconnect->query("SHOW TABLE STATUS LIKE '{$relationTableName}'", [], true);
                if (!$relationTableInfo) {
                    $relationTableType = 'name';
                    $relationTableName = $prefix . $relationName;
                    $relationTableInfo = $dbconnect->query("SHOW TABLE STATUS LIKE '{$relationTableName}'", [], true);
                    if (!$relationTableInfo) {
                        throw new Exception("relation table not found");
                    }
                }
                $relationTableInfo = $relationTableInfo[0];
                $relationModel = $relationModels[$index] ?? '';

                list($relationNamespace, $relationName, $relationFile) = $this->getModelData($modelModuleName, $relationModel, $relationName);

                $relations[] = [
                    //関連テーブルのベース名
                    'relationName'          => $relationName,
                    //関連テーブルクラスの名前空間
                    'relationNamespace'     => $relationNamespace,
                    //関連モデル名
                    'relationModel'         => $relationModel,
                    //関連ファイル
                    'relationFile'          => $relationFile,
                    //関連テーブル名
                    'relationTableName'     => $relationTableName,
                    //関連テーブル情報
                    'relationTableInfo'     => $relationTableInfo,
                    //関連モデルテーブルタイプ(nameまたはtable)
                    'relationTableType'     => $relationTableType,
                    //関連モデルテーブルタイプ名
                    'relationTableTypeName' => $relationTableTypeName,
                    //関連モード
                    'relationFields'        => isset($relationFields[$index]) ? explode(',', $relationFields[$index]) : [],
                    //関連モード
                    'relationMode'          => isset($relationMode[$index]) ? $relationMode[$index] : 'belongsto',
                    //関連モデルコントローラー
                    'relationController'    => isset($relationController[$index]) ? $relationController[$index] : '',
                    //関連テーブル外部キー
                    'relationForeignKey'    => isset($relationForeignKey[$index]) ? $relationForeignKey[$index] : '',
                    //関連テーブル主キー
                    'relationPrimaryKey'    => isset($relationPrimaryKey[$index]) ? $relationPrimaryKey[$index] : '',
                ];
            }
        }

        //テーブル名に応じて対応するFontawesomeアイコン
        $iconPath = ROOT_PATH . str_replace('/', DS, '/public/assets/libs/font-awesome/less/variables.less');
        $iconName = is_file($iconPath) && stripos(file_get_contents($iconPath), '@fa-var-' . $table . ':') ? 'fa fa-' . $table : 'fa fa-circle-o';

        //コントローラー
        list($controllerNamespace, $controllerName, $controllerFile, $controllerArr) = $this->getControllerData($moduleName, $controller, $table);
        //モデル
        list($modelNamespace, $modelName, $modelFile, $modelArr) = $this->getModelData($modelModuleName, $model, $table);
        //バリデーター
        list($validateNamespace, $validateName, $validateFile, $validateArr) = $this->getValidateData($validateModuleName, $validate, $table);

        //ベースファイル名を処理，すべてのアンダースコアを削除して小文字に変換
        $baseNameArr = $controllerArr;
        $baseFileName = Loader::parseName(array_pop($baseNameArr), 0);
        array_push($baseNameArr, $baseFileName);
        $controllerBaseName = strtolower(implode(DS, $baseNameArr));
        //$controllerUrl = strtolower(implode('/', $baseNameArr));
        $controllerUrl = $this->getControllerUrl($moduleName, $baseNameArr);

        //ビュー ファイル
        $viewArr = $controllerArr;
        $lastValue = array_pop($viewArr);
        $viewArr[] = Loader::parseName($lastValue, 0);
        array_unshift($viewArr, 'view');
        $viewDir = $adminPath . strtolower(implode(DS, $viewArr)) . DS;

        //最終的に生成されるファイルパス
        $javascriptFile = ROOT_PATH . 'public' . DS . 'assets' . DS . 'js' . DS . 'backend' . DS . $controllerBaseName . '.js';
        $addFile = $viewDir . 'add.html';
        $editFile = $viewDir . 'edit.html';
        $indexFile = $viewDir . 'index.html';
        $recyclebinFile = $viewDir . 'recyclebin.html';
        $langFile = $adminPath . 'lang' . DS . Lang::detect() . DS . $controllerBaseName . '.php';

        //削除モードかどうか
        $delete = $input->getOption('delete');
        if ($delete) {
            $readyFiles = [$controllerFile, $modelFile, $validateFile, $addFile, $editFile, $indexFile, $recyclebinFile, $langFile, $javascriptFile];
            foreach ($readyFiles as $k => $v) {
                $output->warning($v);
            }
            if (!$force) {
                $output->info("Are you sure you want to delete all those files?  Type 'yes' to continue: ");
                $line = fgets(defined('STDIN') ? STDIN : fopen('php://stdin', 'r'));
                if (trim($line) != 'yes') {
                    throw new Exception("Operation is aborted!");
                }
            }
            foreach ($readyFiles as $k => $v) {
                if (file_exists($v)) {
                    unlink($v);
                }
                //空のフォルダーを削除
                switch ($v) {
                    case $modelFile:
                        $this->removeEmptyBaseDir($v, $modelArr);
                        break;
                    case $validateFile:
                        $this->removeEmptyBaseDir($v, $validateArr);
                        break;
                    case $addFile:
                    case $editFile:
                    case $indexFile:
                    case $recyclebinFile:
                        $this->removeEmptyBaseDir($v, $viewArr);
                        break;
                    default:
                        $this->removeEmptyBaseDir($v, $controllerArr);
                }
            }

            //メニューを続けて削除
            if ($menu) {
                exec("php think menu -c {$controllerUrl} -d 1 -f 1");
            }

            $output->info("Delete Successed");
            return;
        }

        //上書きモードでない場合、コントローラーファイルが存在するとエラーを報告
        if (is_file($controllerFile) && !$force) {
            throw new Exception("controller already exists!\nIf you need to rebuild again, use the parameter --force=true ");
        }

        //上書きモードでない場合、モデルファイルが存在するとエラーを報告
        if (is_file($modelFile) && !$force) {
            throw new Exception("model already exists!\nIf you need to rebuild again, use the parameter --force=true ");
        }

        //上書きモードでない場合、バリデーションファイルが存在するとエラーを報告
        if (is_file($validateFile) && !$force) {
            throw new Exception("validate already exists!\nIf you need to rebuild again, use the parameter --force=true ");
        }

        require $adminPath . 'common.php';

        //データベースからテーブルフィールド情報を取得
        $sql = "SELECT * FROM `information_schema`.`columns` "
            . "WHERE TABLE_SCHEMA = ? AND table_name = ? "
            . "ORDER BY ORDINAL_POSITION";
        //メインテーブルの列を読み込む
        $columnList = $dbconnect->query($sql, [$dbname, $modelTableName]);
        $fieldArr = [];
        foreach ($columnList as $k => $v) {
            $fieldArr[] = $v['COLUMN_NAME'];
        }

        // 関連テーブルの列を読み込む
        foreach ($relations as $index => &$relation) {
            $relationColumnList = $dbconnect->query($sql, [$dbname, $relation['relationTableName']]);

            $relationFieldList = [];
            foreach ($relationColumnList as $k => $v) {
                $relationFieldList[] = $v['COLUMN_NAME'];
            }
            if (!$relation['relationPrimaryKey']) {
                foreach ($relationColumnList as $k => $v) {
                    if ($v['COLUMN_KEY'] == 'PRI') {
                        $relation['relationPrimaryKey'] = $v['COLUMN_NAME'];
                        break;
                    }
                }
            }
            // 主キーが空の場合
            if (!$relation['relationPrimaryKey']) {
                throw new Exception('Relation Primary key not found!');
            }
            // 主キーがテーブルのフィールドに存在しない場合
            if (!in_array($relation['relationPrimaryKey'], $relationFieldList)) {
                throw new Exception('Relation Primary key not found in table!');
            }
            $relation['relationColumnList'] = $relationColumnList;
            $relation['relationFieldList'] = $relationFieldList;
        }
        unset($relation);

        $addList = [];
        $editList = [];
        $javascriptList = [];
        $langList = [];
        $operateButtonList = [];
        $field = 'id';
        $order = 'id';
        $priDefined = false;
        $priKeyArr = [];
        $relationPrimaryKey = '';
        foreach ($columnList as $k => $v) {
            if ($v['COLUMN_KEY'] == 'PRI') {
                $priKeyArr[] = $v['COLUMN_NAME'];
            }
        }
        if (!$priKeyArr) {
            throw new Exception('Primary key not found!');
        }
        if (count($priKeyArr) > 1) {
            throw new Exception('Multiple primary key not support!');
        }
        $priKey = reset($priKeyArr);

        $order = $priKey;

        //関連モデルである場合
        foreach ($relations as $index => &$relation) {
            if ($relation['relationMode'] == 'hasone') {
                $relationForeignKey = $relation['relationForeignKey'] ?: $table . "_id";
                $relationPrimaryKey = $relation['relationPrimaryKey'] ?: $priKey;

                if (!in_array($relationForeignKey, $relation['relationFieldList'])) {
                    throw new Exception('relation table [' . $relation['relationTableName'] . '] must be contain field [' . $relationForeignKey . ']');
                }
                if (!in_array($relationPrimaryKey, $fieldArr)) {
                    throw new Exception('table [' . $modelTableName . '] must be contain field [' . $relationPrimaryKey . ']');
                }
            } elseif ($relation['relationMode'] == 'belongsto') {
                $relationForeignKey = $relation['relationForeignKey'] ?: Loader::parseName($relation['relationName']) . "_id";
                $relationPrimaryKey = $relation['relationPrimaryKey'] ?: $relation['relationPriKey'];
                if (!in_array($relationForeignKey, $fieldArr)) {
                    throw new Exception('table [' . $modelTableName . '] must be contain field [' . $relationForeignKey . ']');
                }
                if (!in_array($relationPrimaryKey, $relation['relationFieldList'])) {
                    throw new Exception('relation table [' . $relation['relationTableName'] . '] must be contain field [' . $relationPrimaryKey . ']');
                }
            } elseif ($relation['relationMode'] == 'hasmany') {
                $relationForeignKey = $relation['relationForeignKey'] ?: $table . "_id";
                $relationPrimaryKey = $relation['relationPrimaryKey'] ?: $priKey;
                if (!in_array($relationForeignKey, $relation['relationFieldList'])) {
                    throw new Exception('relation table [' . $relation['relationTableName'] . '] must be contain field [' . $relationForeignKey . ']');
                }
                if (!in_array($relationPrimaryKey, $fieldArr)) {
                    throw new Exception('table [' . $modelTableName . '] must be contain field [' . $relationPrimaryKey . ']');
                }
                $relation['relationColumnList'] = [];
                $relation['relationFieldList'] = [];
            }
            $relation['relationForeignKey'] = $relationForeignKey;
            $relation['relationPrimaryKey'] = $relationPrimaryKey;
            $relation['relationClassName'] = $modelNamespace != $relation['relationNamespace'] ? $relation['relationNamespace'] . '\\' . $relation['relationName'] : $relation['relationName'];
        }
        unset($relation);

        try {
            Form::setEscapeHtml(false);
            $setAttrArr = [];
            $getAttrArr = [];
            $getEnumArr = [];
            $appendAttrList = [];
            $controllerAssignList = [];
            $headingHtml = '{:build_heading()}';
            $controllerImport = '';
            $importHtml = '';
            $multipleHtml = '';
            $recyclebinHtml = '';

            if ($import) {
                $controllerImport = $this->getReplacedStub('mixins/import', []);
                $importHtml = '<a href="javascript:;" class="btn btn-danger btn-import {:$auth->check(\'' . $controllerUrl . '/import\')?\'\':\'hide\'}" title="{:__(\'Import\')}" id="btn-import-file" data-url="ajax/upload" data-mimetype="csv,xls,xlsx" data-multiple="false"><i class="fa fa-upload"></i> {:__(\'Import\')}</a>';
            }

            //すべてのフィールドをループ,ビューの構築を開始HTMLとJS情報
            foreach ($columnList as $k => $v) {
                $field = $v['COLUMN_NAME'];
                $itemArr = [];
                // ここで構築するEnumとSet型のリストデータ
                if (in_array($v['DATA_TYPE'], ['enum', 'set', 'tinyint']) || $this->headingFilterField == $field) {
                    if ($v['DATA_TYPE'] !== 'tinyint') {
                        $itemArr = substr($v['COLUMN_TYPE'], strlen($v['DATA_TYPE']) + 1, -1);
                        $itemArr = explode(',', str_replace("'", '', $itemArr));
                    }
                    $itemArr = $this->getItemArray($itemArr, $field, $v['COLUMN_COMMENT']);
                    //タイプがtinyintかつ備考データを使用している場合
                    if ($itemArr && !in_array($v['DATA_TYPE'], ['enum', 'set'])) {
                        $v['DATA_TYPE'] = 'enum';
                    }
                }
                // 言語リスト
                if ($v['COLUMN_COMMENT'] != '') {
                    $langList[] = $this->getLangItem($field, $v['COLUMN_COMMENT']);
                }
                $inputType = '';
                //予約フィールドは編集および追加不可
                if ($v['COLUMN_KEY'] != 'PRI' && !in_array($field, $this->reservedField) && !in_array($field, $this->ignoreFields)) {
                    $inputType = $this->getFieldType($v);

                    // もし〜ならnumberタイプが number の場合はステップ値を追加
                    $step = $inputType == 'number' && $v['NUMERIC_SCALE'] > 0 ? "0." . str_repeat(0, $v['NUMERIC_SCALE'] - 1) . "1" : 0;

                    $attrArr = ['id' => "c-{$field}"];
                    $cssClassArr = ['form-control'];
                    $fieldName = "row[{$field}]";
                    $defaultValue = $v['COLUMN_DEFAULT'];
                    $editValue = "{\$row.{$field}|htmlentities}";
                    // デフォルト値がnull,でない場合は必須項目となる
                    if ($v['IS_NULLABLE'] == 'NO') {
                        $attrArr['data-rule'] = 'required';
                    }

                    //フィールドタイプが符号なし型の場合，を設定する<input min=0>
                    if (stripos($v['COLUMN_TYPE'], 'unsigned') !== false) {
                        $attrArr['min'] = 0;
                    }

                    if ($inputType == 'select') {
                        $cssClassArr[] = 'selectpicker';
                        $attrArr['class'] = implode(' ', $cssClassArr);
                        if ($v['DATA_TYPE'] == 'set') {
                            $attrArr['multiple'] = '';
                            $fieldName .= "[]";
                        }
                        $attrArr['name'] = $fieldName;

                        $this->getEnum($getEnumArr, $controllerAssignList, $field, $itemArr, $v['DATA_TYPE'] == 'set' ? 'multiple' : 'select');

                        $itemArr = $this->getLangArray($itemArr, false);
                        //アクセサを追加
                        $this->getAttr($getAttrArr, $field, $v['DATA_TYPE'] == 'set' ? 'multiple' : 'select');
                        if ($v['DATA_TYPE'] == 'set') {
                            $this->setAttr($setAttrArr, $field, $inputType);
                        }
                        $this->appendAttr($appendAttrList, $field);
                        $formAddElement = $this->getReplacedStub('html/select', ['field' => $field, 'fieldName' => $fieldName, 'fieldList' => $this->getFieldListName($field), 'attrStr' => Form::attributes($attrArr), 'selectedValue' => $defaultValue]);
                        $formEditElement = $this->getReplacedStub('html/select', ['field' => $field, 'fieldName' => $fieldName, 'fieldList' => $this->getFieldListName($field), 'attrStr' => Form::attributes($attrArr), 'selectedValue' => "\$row.{$field}"]);
                    } elseif ($inputType == 'datetime') {
                        $cssClassArr[] = 'datetimepicker';
                        $attrArr['class'] = implode(' ', $cssClassArr);
                        $format = "YYYY-MM-DD HH:mm:ss";
                        $phpFormat = "Y-m-d H:i:s";
                        $fieldFunc = '';
                        switch ($v['DATA_TYPE']) {
                            case 'year':
                                $format = "YYYY";
                                $phpFormat = 'Y';
                                break;
                            case 'date':
                                $format = "YYYY-MM-DD";
                                $phpFormat = 'Y-m-d';
                                break;
                            case 'time':
                                $format = "HH:mm:ss";
                                $phpFormat = 'H:i:s';
                                break;
                            case 'timestamp':
                                $fieldFunc = 'datetime';
                            // no break
                            case 'datetime':
                                $format = "YYYY-MM-DD HH:mm:ss";
                                $phpFormat = 'Y-m-d H:i:s';
                                break;
                            default:
                                $fieldFunc = 'datetime';
                                $this->getAttr($getAttrArr, $field, $inputType);
                                $this->setAttr($setAttrArr, $field, $inputType);
                                $this->appendAttr($appendAttrList, $field);
                                break;
                        }
                        $defaultDateTime = "{:date('{$phpFormat}')}";
                        $attrArr['data-date-format'] = $format;
                        $attrArr['data-use-current'] = "true";
                        $formAddElement = Form::text($fieldName, $defaultDateTime, $attrArr);
                        $formEditElement = Form::text($fieldName, ($fieldFunc ? "{:\$row.{$field}?{$fieldFunc}(\$row.{$field}):''}" : "{\$row.{$field}{$fieldFunc}}"), $attrArr);
                    } elseif ($inputType == 'datetimerange') {
                        $cssClassArr[] = 'datetimerange';
                        $attrArr['class'] = implode(' ', $cssClassArr);
                        $attrArr['data-locale'] = '{"format":"YYYY-MM-DD HH:mm:ss"}';
                        $fieldFunc = '';
                        $defaultDateTime = "";
                        $formAddElement = Form::text($fieldName, $defaultDateTime, $attrArr);
                        $formEditElement = Form::text($fieldName, $editValue, $attrArr);
                    } elseif ($inputType == 'checkbox' || $inputType == 'radio') {
                        unset($attrArr['data-rule']);
                        $fieldName = $inputType == 'checkbox' ? $fieldName .= "[]" : $fieldName;
                        $attrArr['name'] = "row[{$fieldName}]";

                        $this->getEnum($getEnumArr, $controllerAssignList, $field, $itemArr, $inputType);
                        $itemArr = $this->getLangArray($itemArr, false);
                        //アクセサを追加
                        $this->getAttr($getAttrArr, $field, $inputType);
                        if ($inputType == 'checkbox') {
                            $this->setAttr($setAttrArr, $field, $inputType);
                        }
                        $this->appendAttr($appendAttrList, $field);
                        $defaultValue = $inputType == 'radio' && !$defaultValue ? key($itemArr) : $defaultValue;

                        $formAddElement = $this->getReplacedStub('html/' . $inputType, ['field' => $field, 'fieldName' => $fieldName, 'fieldList' => $this->getFieldListName($field), 'attrStr' => Form::attributes($attrArr), 'selectedValue' => $defaultValue]);
                        $formEditElement = $this->getReplacedStub('html/' . $inputType, ['field' => $field, 'fieldName' => $fieldName, 'fieldList' => $this->getFieldListName($field), 'attrStr' => Form::attributes($attrArr), 'selectedValue' => "\$row.{$field}"]);
                    } elseif ($inputType == 'textarea' && !$this->isMatchSuffix($field, $this->selectpagesSuffix) && !$this->isMatchSuffix($field, $this->imageField)) {
                        $cssClassArr[] = $this->isMatchSuffix($field, $this->editorSuffix) ? $this->editorClass : '';
                        $attrArr['class'] = implode(' ', $cssClassArr);
                        $attrArr['rows'] = 5;
                        $formAddElement = Form::textarea($fieldName, $defaultValue, $attrArr);
                        $formEditElement = Form::textarea($fieldName, $editValue, $attrArr);
                    } elseif ($inputType == 'switch') {
                        unset($attrArr['data-rule']);
                        if ($defaultValue === '1' || $defaultValue === 'Y') {
                            $yes = $defaultValue;
                            $no = $defaultValue === '1' ? '0' : 'N';
                        } else {
                            $no = $defaultValue;
                            $yes = $defaultValue === '0' ? '1' : 'Y';
                        }
                        if (!$itemArr) {
                            $itemArr = [$yes => 'Yes', $no => 'No'];
                        }
                        $stateNoClass = 'fa-flip-horizontal text-gray';
                        $formAddElement = $this->getReplacedStub('html/' . $inputType, ['field' => $field, 'fieldName' => $fieldName, 'fieldYes' => $yes, 'fieldNo' => $no, 'attrStr' => Form::attributes($attrArr), 'fieldValue' => $defaultValue, 'fieldSwitchClass' => $defaultValue == $no ? $stateNoClass : '']);
                        $formEditElement = $this->getReplacedStub('html/' . $inputType, ['field' => $field, 'fieldName' => $fieldName, 'fieldYes' => $yes, 'fieldNo' => $no, 'attrStr' => Form::attributes($attrArr), 'fieldValue' => "{\$row.{$field}}", 'fieldSwitchClass' => "{eq name=\"\$row.{$field}\" value=\"{$no}\"}fa-flip-horizontal text-gray{/eq}"]);
                    } elseif ($inputType == 'citypicker') {
                        $attrArr['class'] = implode(' ', $cssClassArr);
                        $attrArr['data-toggle'] = "city-picker";
                        $formAddElement = sprintf("<div class='control-relative'>%s</div>", Form::input('text', $fieldName, $defaultValue, $attrArr));
                        $formEditElement = sprintf("<div class='control-relative'>%s</div>", Form::input('text', $fieldName, $editValue, $attrArr));
                    } elseif ($inputType == 'tagsinput') {
                        $attrArr['class'] = implode(' ', $cssClassArr);
                        $attrArr['data-role'] = "tagsinput";
                        $formAddElement = Form::input('text', $fieldName, $defaultValue, $attrArr);
                        $formEditElement = Form::input('text', $fieldName, $editValue, $attrArr);
                    } elseif ($inputType == 'fieldlist') {
                        $itemArr = $this->getItemArray($itemArr, $field, $v['COLUMN_COMMENT']);
                        $templateName = !isset($itemArr['key']) && count($itemArr) > 0 ? (isset($itemArr['value']) && count($itemArr) === 1 ? 'fieldlist-array' : 'fieldlist-template') : 'fieldlist';
                        $itemKey = isset($itemArr['key']) ? ucfirst($itemArr['key']) : 'Key';
                        $itemValue = isset($itemArr['value']) ? ucfirst($itemArr['value']) : 'Value';
                        $theadListArr = $tbodyListArr = [];
                        foreach ($itemArr as $index => $item) {
                            $theadListArr[] = "<td>{:__('" . $item . "')}</td>";
                            $tbodyListArr[] = '<td><input type="text" name="<%=name%>[<%=index%>][' . $index . ']" class="form-control" value="<%=row.' . $index . '%>"/></td>';
                        }
                        $colspan = count($theadListArr) + 1;
                        $commonFields = ['field' => $field, 'fieldName' => $fieldName, 'itemKey' => $itemKey, 'itemValue' => $itemValue, 'theadList' => implode("\n", $theadListArr), 'tbodyList' => implode("\n", $tbodyListArr), 'colspan' => $colspan];
                        $formAddElement = $this->getReplacedStub('html/' . $templateName, array_merge($commonFields, ['fieldValue' => $defaultValue]));
                        $formEditElement = $this->getReplacedStub('html/' . $templateName, array_merge($commonFields, ['fieldValue' => $editValue]));
                    } else {
                        $search = $replace = '';
                        //特殊フィールドは関連検索用
                        if ($this->isMatchSuffix($field, $this->selectpageSuffix)) {
                            $inputType = 'text';
                            $defaultValue = '';
                            $attrArr['data-rule'] = 'required';
                            $cssClassArr[] = 'selectpage';
                            $selectpageTable = substr($field, 0, strripos($field, '_'));
                            $selectpageField = '';
                            foreach ($relations as $index => $relation) {
                                if ($relation['relationForeignKey'] === $field) {
                                    $selectpageTable = substr($relation['relationTableName'], strlen($prefix));
                                    break;
                                }
                            }
                            $selectpageController = str_replace('_', '/', $selectpageTable);
                            $attrArr['data-source'] = $selectpageController . "/index";
                            //種類テーブルの場合は特別な処理が必要
                            if ($selectpageController == 'category') {
                                $attrArr['data-source'] = 'category/selectpage';
                                $attrArr['data-params'] = '##replacetext##';
                                $search = '"##replacetext##"';
                                $replace = '\'{"custom[type]":"' . $table . '"}\'';
                            } elseif ($selectpageController == 'admin') {
                                $attrArr['data-source'] = 'auth/admin/selectpage';
                                $attrArr['data-field'] = 'nickname';
                            } elseif ($selectpageController == 'user') {
                                $attrArr['data-source'] = 'user/user/index';
                                $attrArr['data-field'] = 'nickname';
                            }
                            if ($this->isMatchSuffix($field, $this->selectpagesSuffix)) {
                                $attrArr['data-multiple'] = 'true';
                            }

                            $tableInfo = null;
                            try {
                                $tableInfo = \think\Db::name($selectpageTable)->getTableInfo();
                                if (isset($tableInfo['fields'])) {
                                    foreach ($tableInfo['fields'] as $m => $n) {
                                        if (in_array($n, ['nickname', 'title', 'name'])) {
                                            $selectpageField = $n;
                                            break;
                                        }
                                    }
                                }
                            } catch (\Exception $e) {
                            }
                            if (!$selectpageField) {
                                foreach ($this->fieldSelectpageMap as $m => $n) {
                                    if (in_array($field, $n)) {
                                        $attrArr['data-field'] = $m;
                                        break;
                                    }
                                }
                            }
                        }
                        //オートコンプリートがあるため他の内容も入力可能
                        $step = array_intersect($cssClassArr, ['selectpage']) ? 0 : $step;
                        $attrArr['class'] = implode(' ', $cssClassArr);
                        $isUpload = false;
                        if ($this->isMatchSuffix($field, array_merge($this->imageField, $this->fileField))) {
                            $isUpload = true;
                        }
                        //ステップ値の場合はステップ値を加算
                        if ($step) {
                            $attrArr['step'] = $step;
                        }
                        //画像の場合はsize
                        if ($isUpload) {
                            $attrArr['size'] = 50;
                        }

                        //フィールドのデフォルト値判定
                        if ('NULL' == $defaultValue || "''" == $defaultValue) {
                            $defaultValue = '';
                        }

                        $formAddElement = Form::input($inputType, $fieldName, $defaultValue, $attrArr);
                        $formEditElement = Form::input($inputType, $fieldName, $editValue, $attrArr);
                        if ($search && $replace) {
                            $formAddElement = str_replace($search, $replace, $formAddElement);
                            $formEditElement = str_replace($search, $replace, $formEditElement);
                        }
                        //画像またはファイルの場合
                        if ($isUpload) {
                            $formAddElement = $this->getImageUpload($field, $formAddElement);
                            $formEditElement = $this->getImageUpload($field, $formEditElement);
                        }
                    }
                    //追加と編集用のHTML情報
                    $addList[] = $this->getFormGroup($field, $formAddElement);
                    $editList[] = $this->getFormGroup($field, $formEditElement);
                }

                //フィルタリングtextタイプフィールド
                if ($v['DATA_TYPE'] != 'text' && $inputType != 'fieldlist') {
                    //主キー
                    if ($v['COLUMN_KEY'] == 'PRI' && !$priDefined) {
                        $priDefined = true;
                        $javascriptList[] = "{checkbox: true}";
                    }
                    if ($this->deleteTimeField == $field) {
                        $recyclebinHtml = $this->getReplacedStub('html/recyclebin-html', ['controllerUrl' => $controllerUrl]);
                        continue;
                    }
                    if (!$fields || in_array($field, explode(',', $fields))) {
                        //構築JS列情報
                        $javascriptList[] = $this->getJsColumn($field, $v['DATA_TYPE'], $inputType && in_array($inputType, ['select', 'checkbox', 'radio']) ? '_text' : '', $itemArr, $v);
                    }
                    if ($this->headingFilterField && $this->headingFilterField == $field && $itemArr) {
                        $headingHtml = $this->getReplacedStub('html/heading-html', ['field' => $field, 'fieldName' => Loader::parseName($field, 1, false)]);
                        $multipleHtml = $this->getReplacedStub('html/multiple-html', ['field' => $field, 'fieldName' => Loader::parseName($field, 1, false), 'controllerUrl' => $controllerUrl]);
                    }
                    //ソート方法,ソートフィールドが指定されている場合,指定がない場合は主キーでソート
                    $order = $field == $this->sortField ? $this->sortField : $order;
                }
            }

            //関連テーブルをループ,言語パックとJS列
            foreach ($relations as $index => $relation) {
                if ($relation['relationMode'] == 'hasmany') {
                    $relationFieldText = ucfirst(strtolower($relation['relationName'])) . ' List';
                    // 言語リスト
                    if ($relation['relationTableInfo']['Comment']) {
                        $langList[] = $this->getLangItem($relationFieldText, rtrim($relation['relationTableInfo']['Comment'], "テーブル") . "列テーブル");
                    }

                    $relationTableName = $relation['relationTableName'];
                    $relationTableName = stripos($relationTableName, $prefix) === 0 ? substr($relationTableName, strlen($prefix)) : $relationTableName;

                    list($realtionControllerNamespace, $realtionControllerName, $realtionControllerFile, $realtionControllerArr) = $this->getControllerData($moduleName, $relation['relationController'], $relationTableName);
                    $realtionControllerArr = array_map("strtolower", $realtionControllerArr);
                    if (count($realtionControllerArr) > 1) {
                        $realtionControllerArr = [implode('.', $realtionControllerArr)];
                    }
                    $realtionControllerArr[] = 'index';
                    $realtionControllerArr[] = $relation['relationForeignKey'] . '/{ids}';
                    $relationControllerUrl = implode('/', $realtionControllerArr);

                    //構築JS列情報
                    $operateButtonList[] = "{name: 'addtabs',title: __('{$relationFieldText}'),text: __('{$relationFieldText}'),classname: 'btn btn-xs btn-info btn-dialog',icon: 'fa fa-list',url: '" . $relationControllerUrl . "'}";
                    //echo "php think crud -t {$relation['relationTableName']} -c {$relation['relationController']} -m {$relation['relationModel']} -i " . implode(',', $relation['relationFields']);
                    //関連テーブルのコントローラーが存在しない場合のみ生成を行う
                    if (!is_file($realtionControllerFile)) {
                        exec("php think crud -t {$relation['relationTableName']} -c {$relation['relationController']} -m {$relation['relationModel']} -i " . implode(',', $relation['relationFields']));
                    }
                }
                foreach ($relation['relationColumnList'] as $k => $v) {
                    // 非表示フィールドはそのまま除外
                    if ($relation['relationFields'] && !in_array($v['COLUMN_NAME'], $relation['relationFields'])) {
                        continue;
                    }

                    $relationField = strtolower($relation['relationName']) . "." . $v['COLUMN_NAME'];
                    // 言語リスト
                    if ($v['COLUMN_COMMENT'] != '') {
                        $langList[] = $this->getLangItem($relationField, $v['COLUMN_COMMENT']);
                    }

                    //フィルタリングtextタイプフィールド
                    if ($v['DATA_TYPE'] != 'text') {
                        //構築JS列情報
                        $javascriptList[] = $this->getJsColumn($relationField, $v['DATA_TYPE'], '', [], $v);
                    }
                }
            }

            //JS最後の列に操作列を追加
            $javascriptList[] = str_repeat(" ", 24) . "{field: 'operate', title: __('Operate'), table: table, events: Table.api.events.operate, " . ($operateButtonList ? "buttons: [" . implode(',', $operateButtonList) . "], " : "") . "formatter: Table.api.formatter.operate}";
            $addList = implode("\n", array_filter($addList));
            $editList = implode("\n", array_filter($editList));
            $javascriptList = implode(",\n", array_filter($javascriptList));
            $langList = implode(",\n", array_filter($langList));
            //配列のイコールを揃える
            $langList = array_filter(explode(",\n", $langList . ",\n"));
            foreach ($langList as &$line) {
                if (preg_match("/^\s+'([^']+)'\s*=>\s*'([^']+)'\s*/is", $line, $matches)) {
                    $line = "    '{$matches[1]}'" . str_pad('=>', ($this->fieldMaxLen - strlen($matches[1]) + 3), ' ', STR_PAD_LEFT) . " '{$matches[2]}'";
                }
            }
            unset($line);
            $langList = implode(",\n", array_filter($langList));
            $fixedcolumns = count($columnList) >= 10 ? 1 : $fixedcolumns;

            $fixedColumnsJs = '';
            if (is_numeric($fixedcolumns) && $fixedcolumns) {
                $fixedColumnsJs = "\n" . str_repeat(" ", 16) . "fixedColumns: true,\n" . str_repeat(" ", 16) . ($fixedcolumns < 0 ? "fixedNumber" : "fixedRightNumber") . ": " . $fixedcolumns . ",";
            }

            //テーブルコメント
            $tableComment = $modelTableInfo ? $modelTableInfo['Comment'] : '';
            $tableComment = mb_substr($tableComment, -1) == 'テーブル' ? mb_substr($tableComment, 0, -1) . '管理' : $tableComment;

            $modelInit = '';
            if ($priKey != $order) {
                $modelInit = $this->getReplacedStub('mixins' . DS . 'modelinit', ['order' => $order]);
            }

            $data = [
                'modelConnection'         => $db == 'database' ? '' : "protected \$connection = '{$db}';",
                'controllerNamespace'     => $controllerNamespace,
                'modelNamespace'          => $modelNamespace,
                'validateNamespace'       => $validateNamespace,
                'controllerUrl'           => $controllerUrl,
                'controllerName'          => $controllerName,
                'controllerAssignList'    => implode("\n", $controllerAssignList),
                'modelName'               => $modelName,
                'modelTableName'          => $modelTableName,
                'modelTableType'          => $modelTableType,
                'modelTableTypeName'      => $modelTableTypeName,
                'validateName'            => $validateName,
                'tableComment'            => $tableComment,
                'iconName'                => $iconName,
                'pk'                      => $priKey,
                'order'                   => $order,
                'fixedColumnsJs'          => $fixedColumnsJs,
                'table'                   => $table,
                'tableName'               => $modelTableName,
                'addList'                 => $addList,
                'editList'                => $editList,
                'javascriptList'          => $javascriptList,
                'langList'                => $langList,
                'softDeleteClassPath'     => in_array($this->deleteTimeField, $fieldArr) ? "use traits\model\SoftDelete;" : '',
                'softDelete'              => in_array($this->deleteTimeField, $fieldArr) ? "use SoftDelete;" : '',
                'modelAutoWriteTimestamp' => in_array($this->createTimeField, $fieldArr) || in_array($this->updateTimeField, $fieldArr) ? "'integer'" : 'false',
                'createTime'              => in_array($this->createTimeField, $fieldArr) ? "'{$this->createTimeField}'" : 'false',
                'updateTime'              => in_array($this->updateTimeField, $fieldArr) ? "'{$this->updateTimeField}'" : 'false',
                'deleteTime'              => in_array($this->deleteTimeField, $fieldArr) ? "'{$this->deleteTimeField}'" : 'false',
                'relationSearch'          => $relations ? 'true' : 'false',
                'relationWithList'        => '',
                'relationMethodList'      => '',
                'controllerImport'        => $controllerImport,
                'controllerIndex'         => '',
                'recyclebinJs'            => '',
                'headingHtml'             => $headingHtml,
                'multipleHtml'            => $multipleHtml,
                'importHtml'              => $importHtml,
                'recyclebinHtml'          => $recyclebinHtml,
                'visibleFieldList'        => $fields ? "\$row->visible(['" . implode("','", array_filter(in_array($priKey, explode(',', $fields)) ? explode(',', $fields) : explode(',', $priKey . ',' . $fields))) . "']);" : '',
                'appendAttrList'          => implode(",\n", $appendAttrList),
                'getEnumList'             => implode("\n\n", $getEnumArr),
                'getAttrList'             => implode("\n\n", $getAttrArr),
                'setAttrList'             => implode("\n\n", $setAttrArr),
                'modelInit'               => $modelInit,
            ];

            //関連モデルを使用する場合
            if ($relations) {
                $relationWithList = $relationMethodList = $relationVisibleFieldList = [];
                $relationKeyArr = ['hasone' => 'hasOne', 'belongsto' => 'belongsTo', 'hasmany' => 'hasMany'];
                foreach ($relations as $index => $relation) {
                    //関連付け用のメソッドを作成する必要があります
                    $relation['relationMethod'] = strtolower($relation['relationName']);

                    //関連のモード
                    $relation['relationMode'] = strtolower($relation['relationMode']);
                    $relation['relationMode'] = array_key_exists($relation['relationMode'], $relationKeyArr) ? $relationKeyArr[$relation['relationMode']] : '';

                    //関連フィールド
                    $relation['relationPrimaryKey'] = $relation['relationPrimaryKey'] ? $relation['relationPrimaryKey'] : $priKey;

                    //関連モデルを構築するメソッド
                    $relationMethodList[] = $this->getReplacedStub('mixins' . DS . 'modelrelationmethod' . ($relation['relationMode'] == 'hasMany' ? '-hasmany' : ''), $relation);

                    if ($relation['relationMode'] == 'hasMany') {
                        continue;
                    }

                    //プリロード用のメソッド
                    $relationWithList[] = $relation['relationMethod'];

                    unset($relation['relationColumnList'], $relation['relationFieldList'], $relation['relationTableInfo']);

                    //メインテーブルの表示フィールドを設定している場合，関連テーブルのフィールドを明示的に表示する必要があります
                    if ($fields) {
                        $relationVisibleFieldList[] = "\$row->visible(['{$relation['relationMethod']}']);";
                    }

                    //表示フィールド
                    if ($relation['relationFields']) {
                        $relationVisibleFieldList[] = "\$row->getRelation('" . $relation['relationMethod'] . "')->visible(['" . implode("','", $relation['relationFields']) . "']);";
                    }
                }

                $data['relationWithList'] = "->with(['" . implode("','", $relationWithList) . "'])";
                $data['relationMethodList'] = implode("\n\n", $relationMethodList);
                $data['relationVisibleFieldList'] = implode("\n\t\t\t\t", $relationVisibleFieldList);

                if ($relationWithList) {
                    //オーバーライドが必要ですindexメソッド
                    $data['controllerIndex'] = $this->getReplacedStub('controllerindex', $data);
                }
            } elseif ($fields) {
                $data = array_merge($data, ['relationWithList' => '', 'relationMethodList' => '', 'relationVisibleFieldList' => '']);
                //オーバーライドが必要ですindexメソッド
                $data['controllerIndex'] = $this->getReplacedStub('controllerindex', $data);
            }

            // コントローラーファイルを生成
            $this->writeToFile('controller', $data, $controllerFile);
            // モデルファイルを生成
            $this->writeToFile('model', $data, $modelFile);

            if ($relations) {
                foreach ($relations as $i => $relation) {
                    $relation['modelNamespace'] = $relation['relationNamespace'];
                    if (!is_file($relation['relationFile'])) {
                        // 関連モデルファイルを生成
                        $this->writeToFile('relationmodel', $relation, $relation['relationFile']);
                    }
                }
            }
            // バリデーションファイルを生成
            $this->writeToFile('validate', $data, $validateFile);
            // ビュー文件を生成
            $this->writeToFile('add', $data, $addFile);
            $this->writeToFile('edit', $data, $editFile);
            $this->writeToFile('index', $data, $indexFile);
            if ($recyclebinHtml) {
                $this->writeToFile('recyclebin', $data, $recyclebinFile);
                $recyclebinTitle = in_array('title', $fieldArr) ? 'title' : (in_array('name', $fieldArr) ? 'name' : '');
                $recyclebinTitleJs = $recyclebinTitle ? "\n                        {field: '{$recyclebinTitle}', title: __('" . (ucfirst($recyclebinTitle)) . "'), align: 'left'}," : '';
                $data['recyclebinJs'] = $this->getReplacedStub('mixins/recyclebinjs', ['deleteTimeField' => $this->deleteTimeField, 'recyclebinTitleJs' => $recyclebinTitleJs, 'controllerUrl' => $controllerUrl]);
            }
            // 生成JSファイル
            $this->writeToFile('javascript', $data, $javascriptFile);
            // 言語ファイルを生成
            $this->writeToFile('lang', $data, $langFile);
        } catch (ErrorException $e) {
            throw new Exception("Code: " . $e->getCode() . "\nLine: " . $e->getLine() . "\nMessage: " . $e->getMessage() . "\nFile: " . $e->getFile());
        }

        //続けてメニューを生成
        if ($menu) {
            exec("php think menu -c {$controllerUrl}");
        }

        $output->info("Build Successed");
    }

    protected function getEnum(&$getEnum, &$controllerAssignList, $field, $itemArr = '', $inputType = '')
    {
        if (!in_array($inputType, ['datetime', 'select', 'multiple', 'checkbox', 'radio'])) {
            return;
        }
        $fieldList = $this->getFieldListName($field);
        $methodName = 'get' . ucfirst($fieldList);
        foreach ($itemArr as $k => &$v) {
            $v = "__('" . mb_ucfirst($v) . "')";
        }
        unset($v);
        $itemString = $this->getArrayString($itemArr);
        $getEnum[] = <<<EOD
    public function {$methodName}()
    {
        return [{$itemString}];
    }
EOD;
        $controllerAssignList[] = <<<EOD
        \$this->view->assign("{$fieldList}", \$this->model->{$methodName}());
EOD;
    }

    protected function getAttr(&$getAttr, $field, $inputType = '')
    {
        if (!in_array($inputType, ['datetime', 'select', 'multiple', 'checkbox', 'radio'])) {
            return;
        }
        $attrField = ucfirst($this->getCamelizeName($field));
        $getAttr[] = $this->getReplacedStub("mixins" . DS . $inputType, ['field' => $field, 'methodName' => "get{$attrField}TextAttr", 'listMethodName' => "get{$attrField}List"]);
    }

    protected function setAttr(&$setAttr, $field, $inputType = '')
    {
        if (!in_array($inputType, ['datetime', 'checkbox', 'select'])) {
            return;
        }
        $attrField = ucfirst($this->getCamelizeName($field));
        if ($inputType == 'datetime') {
            $return = <<<EOD
return \$value === '' ? null : (\$value && !is_numeric(\$value) ? strtotime(\$value) : \$value);
EOD;
        } elseif (in_array($inputType, ['checkbox', 'select'])) {
            $return = <<<EOD
return is_array(\$value) ? implode(',', \$value) : \$value;
EOD;
        }
        $setAttr[] = <<<EOD
    protected function set{$attrField}Attr(\$value)
    {
        $return
    }
EOD;
    }

    protected function appendAttr(&$appendAttrList, $field)
    {
        $appendAttrList[] = <<<EOD
        '{$field}_text'
EOD;
    }

    /**
     * 対応する空ディレクトリを削除
     * @param $parseFile
     * @param $parseArr
     * @return bool
     */
    protected function removeEmptyBaseDir($parseFile, $parseArr)
    {
        if (count($parseArr) > 1) {
            $parentDir = dirname($parseFile);
            for ($i = 0; $i < count($parseArr); $i++) {
                try {
                    $iterator = new \FilesystemIterator($parentDir);
                    $isDirEmpty = !$iterator->valid();
                    if ($isDirEmpty) {
                        rmdir($parentDir);
                        $parentDir = dirname($parentDir);
                    } else {
                        return true;
                    }
                } catch (\UnexpectedValueException $e) {
                    return false;
                }
            }
        }
        return true;
    }

    /**
     * コントローラーを取得URL
     * @param string $moduleName
     * @param array  $baseNameArr
     * @return string
     */
    protected function getControllerUrl($moduleName, $baseNameArr)
    {
        for ($i = 0; $i < count($baseNameArr) - 1; $i++) {
            $temp = array_slice($baseNameArr, 0, $i + 1);
            $temp[$i] = ucfirst($temp[$i]);
            $controllerFile = APP_PATH . $moduleName . DS . 'controller' . DS . implode(DS, $temp) . '.php';
            //親ディレクトリに同名コントローラーが存在するか確認，存在する場合は変更URL形式
            if (is_file($controllerFile)) {
                $baseNameArr = [implode('.', $baseNameArr)];
                break;
            }
        }
        $controllerUrl = strtolower(implode('/', $baseNameArr));
        return $controllerUrl;
    }

    /**
     * コントローラー関連情報を取得
     * @param $module
     * @param $controller
     * @param $table
     * @return array
     */
    protected function getControllerData($module, $controller, $table)
    {
        return $this->getParseNameData($module, $controller, $table, 'controller');
    }

    /**
     * モデル関連情報を取得
     * @param $module
     * @param $model
     * @param $table
     * @return array
     */
    protected function getModelData($module, $model, $table)
    {
        return $this->getParseNameData($module, $model, $table, 'model');
    }

    /**
     * バリデーター関連情報を取得
     * @param $module
     * @param $validate
     * @param $table
     * @return array
     */
    protected function getValidateData($module, $validate, $table)
    {
        return $this->getParseNameData($module, $validate, $table, 'validate');
    }

    /**
     * 解析済み関連情報を取得
     * @param string $module モジュール名
     * @param string $name   カスタム名
     * @param string $table  テーブル名
     * @param string $type   解析タイプ，本例ではcontroller、model、validate
     * @return array
     */
    protected function getParseNameData($module, $name, $table, $type)
    {
        $arr = [];
        if (!$name) {
            $parseName = Loader::parseName($table, 1);
            $name = str_replace('_', '/', $table);
        }

        $name = str_replace(['.', '/', '\\'], '/', $name);
        $arr = explode('/', $name);
        $parseName = ucfirst(array_pop($arr));
        $parseArr = $arr;
        array_push($parseArr, $parseName);
        //クラス名は内部キーワードにはできません
        if (in_array(strtolower($parseName), $this->internalKeywords)) {
            throw new Exception('Unable to use internal variable:' . $parseName);
        }
        $appNamespace = Config::get('app_namespace');
        $parseNamespace = "{$appNamespace}\\{$module}\\{$type}" . ($arr ? "\\" . implode("\\", $arr) : "");
        $moduleDir = APP_PATH . $module . DS;
        $parseFile = $moduleDir . $type . DS . ($arr ? implode(DS, $arr) . DS : '') . $parseName . '.php';
        return [$parseNamespace, $parseName, $parseFile, $parseArr];
    }

    /**
     * ファイルへ書き込み
     * @param string $name
     * @param array  $data
     * @param string $pathname
     * @return mixed
     */
    protected function writeToFile($name, $data, $pathname)
    {
        foreach ($data as $index => &$datum) {
            $datum = is_array($datum) ? '' : $datum;
        }
        unset($datum);
        $content = $this->getReplacedStub($name, $data);

        if (!is_dir(dirname($pathname))) {
            mkdir(dirname($pathname), 0755, true);
        }
        return file_put_contents($pathname, $content);
    }

    /**
     * 置換後のデータを取得
     * @param string $name
     * @param array  $data
     * @return string
     */
    protected function getReplacedStub($name, $data)
    {
        foreach ($data as $index => &$datum) {
            $datum = is_array($datum) ? '' : $datum;
        }
        unset($datum);
        $search = $replace = [];
        foreach ($data as $k => $v) {
            $search[] = "{%{$k}%}";
            $replace[] = $v;
        }
        $stubname = $this->getStub($name);
        if (isset($this->stubList[$stubname])) {
            $stub = $this->stubList[$stubname];
        } else {
            $this->stubList[$stubname] = $stub = file_get_contents($stubname);
        }
        $content = str_replace($search, $replace, $stub);
        return $content;
    }

    /**
     * ベーステンプレートを取得
     * @param string $name
     * @return string
     */
    protected function getStub($name)
    {
        return __DIR__ . DS . 'Crud' . DS . 'stubs' . DS . $name . '.stub';
    }

    protected function getLangItem($field, $content)
    {
        if ($content || !Lang::has($field)) {
            $this->fieldMaxLen = strlen($field) > $this->fieldMaxLen ? strlen($field) : $this->fieldMaxLen;
            $content = str_replace('，', ',', $content);
            if (stripos($content, ':') !== false && stripos($content, '=') !== false) {
                list($fieldLang, $item) = explode(':', $content);
                $itemArr = [$field => $fieldLang];
                foreach (explode(',', $item) as $k => $v) {
                    $valArr = explode('=', $v);
                    if (count($valArr) == 2) {
                        list($key, $value) = $valArr;
                        $itemArr[$field . ' ' . $key] = $value;
                        if ($this->headingFilterField == $field) {
                            $itemArr['Set ' . $field . ' to ' . $key] = 'に設定すると' . $value;
                        }
                        $this->fieldMaxLen = strlen($field . ' ' . $key) > $this->fieldMaxLen ? strlen($field . ' ' . $key) : $this->fieldMaxLen;
                    }
                }
            } else {
                $itemArr = [$field => $content];
            }
            $resultArr = [];
            foreach ($itemArr as $k => $v) {
                $resultArr[] = "    '" . mb_ucfirst($k) . "' => '{$v}'";
            }
            return implode(",\n", $resultArr);
        } else {
            return '';
        }
    }

    /**
     * データと言語配列リストを読み込む
     * @param array   $arr
     * @param boolean $withTpl
     * @return array
     */
    protected function getLangArray($arr, $withTpl = true)
    {
        $langArr = [];
        foreach ($arr as $k => $v) {
            $langArr[$k] = is_numeric($k) ? ($withTpl ? "{:" : "") . "__('" . mb_ucfirst($v) . "')" . ($withTpl ? "}" : "") : $v;
        }
        return $langArr;
    }

    /**
     * データを文字列付きに変換する
     * @param array $arr
     * @return string
     */
    protected function getArrayString($arr)
    {
        if (!is_array($arr)) {
            return $arr;
        }
        $stringArr = [];
        foreach ($arr as $k => $v) {
            $is_var = in_array(substr($v, 0, 1), ['$', '_']);
            if (!$is_var) {
                $v = str_replace("'", "\'", $v);
                $k = str_replace("'", "\'", $k);
            }
            $stringArr[] = "'" . $k . "' => " . ($is_var ? $v : "'{$v}'");
        }
        return implode(", ", $stringArr);
    }

    protected function getItemArray($item, $field, $comment)
    {
        $itemArr = [];
        $comment = str_replace('，', ',', $comment);
        if (stripos($comment, ':') !== false && stripos($comment, '=') !== false) {
            list($fieldLang, $item) = explode(':', $comment);
            $itemArr = [];
            foreach (explode(',', $item) as $k => $v) {
                $valArr = explode('=', $v);
                if (count($valArr) == 2) {
                    list($key, $value) = $valArr;
                    $itemArr[$key] = $field . ' ' . $key;
                }
            }
        } else {
            foreach ($item as $k => $v) {
                $itemArr[$v] = is_numeric($v) ? $field . ' ' . $v : $v;
            }
        }
        return $itemArr;
    }

    protected function getFieldType(&$v)
    {
        $inputType = 'text';
        switch ($v['DATA_TYPE']) {
            case 'bigint':
            case 'int':
            case 'mediumint':
            case 'smallint':
            case 'tinyint':
                $inputType = 'number';
                break;
            case 'enum':
            case 'set':
                $inputType = 'select';
                break;
            case 'decimal':
            case 'double':
            case 'float':
                $inputType = 'number';
                break;
            case 'longtext':
            case 'text':
            case 'mediumtext':
            case 'smalltext':
            case 'tinytext':
                $inputType = 'textarea';
                break;
            case 'year':
            case 'date':
            case 'time':
            case 'datetime':
            case 'timestamp':
                $inputType = 'datetime';
                break;
            default:
                break;
        }
        $fieldsName = $v['COLUMN_NAME'];
        // 指定されたサフィックスは時間フィールドであることを示します
        if ($this->isMatchSuffix($fieldsName, $this->intDateSuffix)) {
            $inputType = 'datetime';
        }
        // 指定されたサフィックスで終わり、かつタイプがenum,ラジオボタンであることを示します
        if ($this->isMatchSuffix($fieldsName, $this->enumRadioSuffix) && $v['DATA_TYPE'] == 'enum') {
            $inputType = "radio";
        }
        // 指定されたサフィックスで終わり、かつタイプがset,チェックボックスであることを示します
        if ($this->isMatchSuffix($fieldsName, $this->setCheckboxSuffix) && $v['DATA_TYPE'] == 'set') {
            $inputType = "checkbox";
        }
        // 指定されたサフィックスで終わり、かつタイプがcharまたはtinyintかつ長さが1,であることを示すSwitchチェックボックス
        if ($this->isMatchSuffix($fieldsName, $this->switchSuffix) && ($v['COLUMN_TYPE'] == 'tinyint(1)' || $v['COLUMN_TYPE'] == 'char(1)') && $v['COLUMN_DEFAULT'] !== '' && $v['COLUMN_DEFAULT'] !== null) {
            $inputType = "switch";
        }
        // 指定されたサフィックスで終わる都市選択ボックス
        if ($this->isMatchSuffix($fieldsName, $this->citySuffix) && ($v['DATA_TYPE'] == 'varchar' || $v['DATA_TYPE'] == 'char')) {
            $inputType = "citypicker";
        }
        // 指定されたサフィックスで終わる都市選択ボックス
        if ($this->isMatchSuffix($fieldsName, $this->rangeSuffix) && ($v['DATA_TYPE'] == 'varchar' || $v['DATA_TYPE'] == 'char')) {
            $inputType = "datetimerange";
        }
        // 指定されたサフィックスで終わるJSON設定
        if ($this->isMatchSuffix($fieldsName, $this->jsonSuffix) && ($v['DATA_TYPE'] == 'varchar' || $v['DATA_TYPE'] == 'text')) {
            $inputType = "fieldlist";
        }
        // 指定されたサフィックスで終わるタグ設定
        if ($this->isMatchSuffix($fieldsName, $this->tagSuffix) && ($v['DATA_TYPE'] == 'varchar' || $v['DATA_TYPE'] == 'text')) {
            $inputType = "tagsinput";
        }
        return $inputType;
    }

    /**
     * 指定されたサフィックスに合致するかどうかを判定
     * @param string $field     フィールド名
     * @param mixed  $suffixArr サフィックス
     * @return boolean
     */
    protected function isMatchSuffix($field, $suffixArr)
    {
        $suffixArr = is_array($suffixArr) ? $suffixArr : explode(',', $suffixArr);
        foreach ($suffixArr as $k => $v) {
            if (preg_match("/{$v}$/i", $field)) {
                return true;
            }
        }
        return false;
    }

    /**
     * フォームグループデータを取得
     * @param string $field
     * @param string $content
     * @return string
     */
    protected function getFormGroup($field, $content)
    {
        $langField = mb_ucfirst($field);
        return <<<EOD
    <div class="form-group">
        <label class="control-label col-xs-12 col-sm-2">{:__('{$langField}')}:</label>
        <div class="col-xs-12 col-sm-8">
            {$content}
        </div>
    </div>
EOD;
    }

    /**
     * 画像テンプレートデータを取得
     * @param string $field
     * @param string $content
     * @return string
     */
    protected function getImageUpload($field, $content)
    {
        $uploadfilter = $selectfilter = '';
        if ($this->isMatchSuffix($field, $this->imageField)) {
            $uploadfilter = ' data-mimetype="image/gif,image/jpeg,image/png,image/jpg,image/bmp,image/webp"';
            $selectfilter = ' data-mimetype="image/*"';
        }
        $multiple = substr($field, -1) == 's' ? ' data-multiple="true"' : ' data-multiple="false"';
        $preview = ' data-preview-id="p-' . $field . '"';
        $previewcontainer = $preview ? '<ul class="row list-inline faupload-preview" id="p-' . $field . '"></ul>' : '';
        return <<<EOD
<div class="input-group">
                {$content}
                <div class="input-group-addon no-border no-padding">
                    <span><button type="button" id="faupload-{$field}" class="btn btn-danger faupload" data-input-id="c-{$field}"{$uploadfilter}{$multiple}{$preview}><i class="fa fa-upload"></i> {:__('Upload')}</button></span>
                    <span><button type="button" id="fachoose-{$field}" class="btn btn-primary fachoose" data-input-id="c-{$field}"{$selectfilter}{$multiple}><i class="fa fa-list"></i> {:__('Choose')}</button></span>
                </div>
                <span class="msg-box n-right" for="c-{$field}"></span>
            </div>
            {$previewcontainer}
EOD;
    }

    /**
     * 取得JS列データ
     * @param string $field
     * @param string $datatype
     * @param string $extend
     * @param array  $itemArr
     * @param array  $fieldConfig
     * @return string
     */
    protected function getJsColumn($field, $datatype = '', $extend = '', $itemArr = [], $fieldConfig = [])
    {
        $lang = mb_ucfirst($field);
        $formatter = '';
        foreach ($this->fieldFormatterSuffix as $k => $v) {
            if (preg_match("/{$k}$/i", $field)) {
                if (is_array($v)) {
                    if (in_array($datatype, $v['type'])) {
                        $formatter = $v['name'];
                        break;
                    }
                } else {
                    $formatter = $v;
                    break;
                }
            }
        }
        $html = str_repeat(" ", 24) . "{field: '{$field}', title: __('{$lang}')";

        if ($datatype == 'set') {
            $formatter = 'label';
        }
        foreach ($itemArr as $k => &$v) {
            if (substr($v, 0, 3) !== '__(') {
                $v = "__('" . mb_ucfirst($v) . "')";
            }
        }
        unset($v);
        $searchList = json_encode($itemArr, JSON_FORCE_OBJECT | JSON_UNESCAPED_UNICODE);
        $searchList = str_replace(['":"', '"}', ')","'], ['":', '}', '),"'], $searchList);
        if ($itemArr) {
            $html .= ", searchList: " . $searchList;
        }

        // ファイル、画像、権重などのフィールドはデフォルトで検索バーに追加しません，文字列型はデフォルトでLIKE
        $noSearchFiles = ['file$', 'files$', 'image$', 'images$', '^weigh$'];
        if (preg_match("/" . implode('|', $noSearchFiles) . "/i", $field)) {
            $html .= ", operate: false";
        } elseif (in_array($datatype, ['varchar'])) {
            $html .= ", operate: 'LIKE'";
        }

        if (in_array($datatype, ['date', 'datetime']) || $formatter === 'datetime') {
            $html .= ", operate:'RANGE', addclass:'datetimerange', autocomplete:false";
        } elseif (in_array($datatype, ['float', 'double', 'decimal'])) {
            $html .= ", operate:'BETWEEN'";
        }
        if (in_array($datatype, ['set'])) {
            $html .= ", operate:'FIND_IN_SET'";
        }
        if (isset($fieldConfig['CHARACTER_MAXIMUM_LENGTH']) && $fieldConfig['CHARACTER_MAXIMUM_LENGTH'] >= 255 && in_array($datatype, ['varchar']) && !$formatter) {
            $formatter = 'content';
            $html .= ", table: table, class: 'autocontent'";
        }
        if (in_array($formatter, ['image', 'images'])) {
            $html .= ", events: Table.api.events.image";
        }
        if (in_array($formatter, ['toggle'])) {
            $html .= ", table: table";
        }
        if ($itemArr && !$formatter) {
            $formatter = 'normal';
        }
        if ($formatter) {
            $html .= ", formatter: Table.api.formatter." . $formatter . "}";
        } else {
            $html .= "}";
        }
        return $html;
    }

    protected function getCamelizeName($uncamelized_words, $separator = '_')
    {
        $uncamelized_words = $separator . str_replace($separator, " ", strtolower($uncamelized_words));
        return ltrim(str_replace(" ", "", ucwords($uncamelized_words)), $separator);
    }

    protected function getFieldListName($field)
    {
        return $this->getCamelizeName($field) . 'List';
    }
}
