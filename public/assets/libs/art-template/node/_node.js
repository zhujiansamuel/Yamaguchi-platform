var fs = require('fs');
var path = require('path');

module.exports = function (template) {

	var cacheStore = template.cache;
	var defaults = template.defaults;
	var rExtname;

	// 新しい設定フィールドを提供
	defaults.base = '';
	defaults.extname = '.html';
	defaults.encoding = 'utf-8';

	function compileFromFS(filename) {
		// テンプレートを読み込みコンパイル
		var source = readTemplate(filename);

		if (typeof source === 'string') {
			return template.compile(source, {
				filename: filename
			});
		}
	}

	// エンジンのコンパイル結果取得メソッドを上書き
	template.get = function (filename) {
		
	    var fn;


	    if (cacheStore.hasOwnProperty(filename)) {
	        // メモリキャッシュを使用
	        fn = cacheStore[filename];
	    } else {
			fn = compileFromFS(filename);
	    }

	    return fn;
	};

	
	function readTemplate (id) {
	    id = path.join(defaults.base, id + defaults.extname);
	    
	    if (id.indexOf(defaults.base) !== 0) {
	        // セキュリティ制限：テンプレートディレクトリ外のファイル呼び出しを禁止
	        throw new Error('"' + id + '" is not in the template directory');
	    } else {
	        try {
	            return fs.readFileSync(id, defaults.encoding);
	        } catch (e) {}
	    }
	}


	// テンプレートを再実装`include``文の実装方法，テンプレートを絶対パスに変換
	template.utils.$include = function (filename, data, from) {
	    
	    from = path.dirname(from);
	    filename = path.join(from, filename);
	    
	    return template.renderFile(filename, data);
	}


	// express support
	template.__express = function (file, options, fn) {

	    if (typeof options === 'function') {
	        fn = options;
	        options = {};
	    }


		if (!rExtname) {
			// 削除した express 渡されたパス
			rExtname = new RegExp((defaults.extname + '$').replace(/\./g, '\\.'));
		}


	    file = file.replace(rExtname, '');

	    options.filename = file;
	    fn(null, template.renderFile(file, options));
	};


	return template;
}