/**
 * テンプレートをレンダリング
 * @name    template.render
 * @param   {String}    テンプレート
 * @param   {Object}    データ
 * @return  {String}    レンダリング済み文字列
 */
template.render = function (source, options) {
    return compile(source)(options);
};


