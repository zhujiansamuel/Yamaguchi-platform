/**
 * テンプレートのヘルパーメソッドを追加
 * @name    template.helper
 * @param   {String}    名称
 * @param   {Function}  メソッド
 */
template.helper = function (name, helper) {
    helpers[name] = helper;
};

var helpers = template.helpers = utils.$helpers;




