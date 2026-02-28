/**
 * テンプレートエンジン
 * @name    template
 * @param   {String}            テンプレート名
 * @param   {Object, String}    データ。文字列の場合はコンパイルして結果をキャッシュする
 * @return  {String, Function}  レンダリング済みHTML文字列またはレンダリングメソッド
 */
var template = function (filename, content) {
    return typeof content === 'string'
    ?   compile(content, {
            filename: filename
        })
    :   renderFile(filename, content);
};


template.version = '3.0.0';


