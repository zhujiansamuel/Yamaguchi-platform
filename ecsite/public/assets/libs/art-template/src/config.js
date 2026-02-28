/**
 * グローバル設定を行う
 * @name    template.config
 * @param   {String}    名称
 * @param   {Any}       値
 */
template.config = function (name, value) {
    defaults[name] = value;
};



var defaults = template.defaults = {
    openTag: '<%',    // ロジック構文の開始タグ
    closeTag: '%>',   // ロジック構文の終了タグ
    escape: true,     // 変数の HTML 文字をエスケープ出力するかどうか HTML 文字
    cache: true,      // キャッシュを有効にするかどうか（依存 options の filename フィールド）
    compress: false,  // 出力を圧縮するかどうか
    parser: null      // カスタム構文フォーマッタ @see: template-syntax.js
};


