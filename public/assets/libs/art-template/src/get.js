/**
 * コンパイルキャッシュを取得（外部からこのメソッドを上書き可能）（外部からこのメソッドを上書き可能）
 * @param   {String}    テンプレート名
 * @param   {Function}  コンパイル済み関数
 */
template.get = function (filename) {

    var cache;
    
    if (cacheStore[filename]) {
        // メモリキャッシュを使用
        cache = cacheStore[filename];
    } else if (typeof document === 'object') {
        // テンプレートを読み込みコンパイル
        var elem = document.getElementById(filename);
        
        if (elem) {
            var source = (elem.value || elem.innerHTML)
            .replace(/^\s*|\s*$/g, '');
            cache = compile(source, {
                filename: filename
            });
        }
    }

    return cache;
};


