<?php

return [
    [
        'name'    => 'classname',
        'title'   => 'テキストボックス要素をレンダリング',
        'type'    => 'string',
        'content' => [],
        'value'   => '.editor',
        'rule'    => 'required',
        'msg'     => '',
        'tip'     => '指定した要素をレンダリングするために使用，通常は変更不要',
        'ok'      => '',
        'extend'  => '',
    ],
    [
        'name'    => 'height',
        'title'   => 'デフォルトの高さ',
        'type'    => 'string',
        'content' => [],
        'value'   => '250',
        'rule'    => 'required',
        'msg'     => '',
        'tip'     => 'エディターのデフォルトの高さ，auto自動調整の高さを示します',
        'ok'      => '',
        'extend'  => '',
    ],
    [
        'name'    => 'minHeight',
        'title'   => 'デフォルトの高さ',
        'type'    => 'number',
        'content' => [],
        'value'   => '250',
        'rule'    => 'required',
        'msg'     => '',
        'tip'     => 'エディターの最小高さ',
        'ok'      => '',
        'extend'  => '',
    ],
    [
        'name'    => 'followingToolbar',
        'title'   => 'ツールバーを固定表示するか',
        'type'    => 'radio',
        'content' => [
            1 => 'はい',
            0 => 'いいえ',
        ],
        'value'   => '0',
        'rule'    => 'required',
        'msg'     => '',
        'tip'     => 'ツールバーを固定表示するか，通常は自動調整の高さを設定する場合に使用します',
        'ok'      => '',
        'extend'  => '',
    ],
    [
        'name'    => 'airMode',
        'title'   => 'インラインモード',
        'type'    => 'radio',
        'content' => [
            1 => 'はい',
            0 => 'いいえ',
        ],
        'value'   => '0',
        'rule'    => 'required',
        'msg'     => '',
        'tip'     => 'インラインモードを有効にするとツールバーは無効になります',
        'ok'      => '',
        'extend'  => '',
    ],
    [
        'name'    => 'toolbar',
        'title'   => 'デフォルトのツールバー設定',
        'type'    => 'text',
        'content' => [],
        'value'   => '[' . "\r\n"
            . '	["style", ["style", "undo", "redo"]],' . "\r\n"
            . '	["font", ["bold", "underline", "strikethrough", "clear"]],' . "\r\n"
            . '	["fontname", ["color", "fontname", "fontsize"]],' . "\r\n"
            . '	["para", ["ul", "ol", "paragraph", "height"]],' . "\r\n"
            . '	["table", ["table", "hr"]],' . "\r\n"
            . '	["insert", ["link", "picture", "video"]],' . "\r\n"
            . '	["select", ["image", "attachment"]],' . "\r\n"
            . '	["view", ["fullscreen", "codeview", "help"]]' . "\r\n"
            . ']',
        'rule'    => 'required',
        'msg'     => '',
        'tip'     => '',
        'ok'      => '',
        'extend'  => 'rows=10',
    ],
    [
        'name'    => 'placeholder',
        'title'   => 'デフォルトのプレースホルダーテキスト',
        'type'    => 'string',
        'content' => [],
        'value'   => '',
        'rule'    => '',
        'msg'     => '',
        'tip'     => '',
        'ok'      => '',
        'extend'  => '',
    ],
    [
        'name'    => '__tips__',
        'title'   => 'ご案内',
        'type'    => 'string',
        'content' => [],
        'value'   => 'ツールバーの設定はドキュメントを参照してください：https://summernote.org/deep-dive/',
        'rule'    => '',
        'msg'     => '',
        'tip'     => '',
        'ok'      => '',
        'extend'  => '',
    ],
];
