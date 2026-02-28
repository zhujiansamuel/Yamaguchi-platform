/**
 * テンプレートをレンダリング(テンプレート名に基づく)
 * @name    template.render
 * @param   {String}    テンプレート名
 * @param   {Object}    データ
 * @return  {String}    レンダリング済み文字列
 */
var renderFile = template.renderFile = function (filename, data) {
    var fn = template.get(filename) || showDebugInfo({
        filename: filename,
        name: 'Render Error',
        message: 'Template not found'
    });
    return data ? fn(data) : fn;
};


