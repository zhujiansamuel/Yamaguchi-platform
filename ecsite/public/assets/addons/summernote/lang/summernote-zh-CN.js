/*!
 *
 * Super simple WYSIWYG editor v0.8.20
 * https://summernote.org
 *
 *
 * Copyright 2013- Alan Hong and contributors
 * Summernote may be freely distributed under the MIT license.
 *
 * Date: 2021-10-14T21:15Z
 *
 */
(function webpackUniversalModuleDefinition(root, factory) {
	if(typeof exports === 'object' && typeof module === 'object')
		module.exports = factory();
	else if(typeof define === 'function' && define.amd)
		define([], factory);
	else {
		var a = factory();
		for(var i in a) (typeof exports === 'object' ? exports : root)[i] = a[i];
	}
})(self, function() {
return /******/ (() => { // webpackBootstrap
var __webpack_exports__ = {};
(function ($) {
  $.extend($.summernote.lang, {
    'zh-CN': {
      font: {
        bold: '太字',
        italic: '斜体',
        underline: 'アンダースコア',
        clear: '書式をクリア',
        height: '行間',
        name: 'フォント',
        strikethrough: '取り消し線',
        subscript: '下付き',
        superscript: '上付き',
        size: '文字サイズ'
      },
      image: {
        image: '画像',
        insert: '画像を挿入',
        resizeFull: '拡大縮小 100%',
        resizeHalf: '拡大縮小 50%',
        resizeQuarter: '拡大縮小 25%',
        floatLeft: '左寄せフロート',
        floatRight: '右寄せフロート',
        floatNone: 'フロート解除',
        shapeRounded: '形状: 角丸',
        shapeCircle: '形状: 円形',
        shapeThumbnail: '形状: サムネイル',
        shapeNone: '形状: 拡張なし',
        dragImageHere: 'ここに画像をドラッグしてください',
        dropImage: '画像またはテキストをドラッグ',
        selectFromFiles: 'ローカルからアップロード',
        maximumFileSize: '最大ファイルサイズ',
        maximumFileSizeError: 'ファイルサイズが最大値を超えています。',
        url: '画像のURL',
        remove: '画像を削除',
        original: '元の画像'
      },
      video: {
        video: '動画',
        videoLink: '動画リンク',
        insert: '動画を挿入',
        url: '動画のURL',
        providers: '(動画のURL)'
      },
      link: {
        link: 'リンク',
        insert: 'リンクを挿入',
        unlink: 'リンクを削除',
        edit: 'リンクを編集',
        textToDisplay: '表示テキスト',
        url: 'リンクのURL',
        openInNewWindow: '新しいウィンドウで開く'
      },
      table: {
        table: '表',
        addRowAbove: '上に行を挿入',
        addRowBelow: '下に行を挿入',
        addColLeft: '左に列を挿入',
        addColRight: '右に列を挿入',
        delRow: '行を削除',
        delCol: '列を削除',
        delTable: '表を削除'
      },
      hr: {
        insert: '横罫線'
      },
      style: {
        style: 'スタイル',
        p: '標準',
        blockquote: '参照',
        pre: 'コード',
        h1: '見出し 1',
        h2: '見出し 2',
        h3: '見出し 3',
        h4: '見出し 4',
        h5: '見出し 5',
        h6: '見出し 6'
      },
      lists: {
        unordered: '箇条書きリスト',
        ordered: '番号付きリスト'
      },
      options: {
        help: 'ヘルプ',
        fullscreen: '全画面表示',
        codeview: 'ソースコード'
      },
      paragraph: {
        paragraph: '段落',
        outdent: 'インデントを減らす',
        indent: 'インデントを増やす',
        left: '左揃え',
        center: '中央揃え',
        right: '右揃え',
        justify: '両端揃え'
      },
      color: {
        recent: '最近使用した項目',
        more: 'その他',
        background: '背景',
        foreground: '前景色',
        transparent: '透明',
        setTransparent: '透明',
        reset: 'リセット',
        resetToDefault: 'デフォルト'
      },
      shortcut: {
        shortcuts: 'ショートカットキー',
        close: '無効',
        textFormatting: 'テキストの書式',
        action: 'アクション',
        paragraphFormatting: '段落書式',
        documentStyle: 'ドキュメントスタイル',
        extraKeys: '追加キー'
      },
      help: {
        insertParagraph: '段落を挿入',
        undo: '元に戻す',
        redo: 'やり直す',
        tab: 'インデントを増やす',
        untab: 'インデントを減らす',
        bold: '太字',
        italic: '斜体',
        underline: 'アンダースコア',
        strikethrough: '取り消し線',
        removeFormat: '書式をクリア',
        justifyLeft: '左揃え',
        justifyCenter: '中央揃え',
        justifyRight: '右揃え',
        justifyFull: '両端揃え',
        insertUnorderedList: '箇条書きリスト',
        insertOrderedList: '番号付きリスト',
        outdent: 'インデントを減らす',
        indent: 'インデントを増やす',
        formatPara: '選択した内容のスタイルを設定 標準',
        formatH1: '選択した内容のスタイルを設定 見出し1',
        formatH2: '選択した内容のスタイルを設定 見出し2',
        formatH3: '選択した内容のスタイルを設定 見出し3',
        formatH4: '選択した内容のスタイルを設定 見出し4',
        formatH5: '選択した内容のスタイルを設定 見出し5',
        formatH6: '選択した内容のスタイルを設定 見出し6',
        insertHorizontalRule: '横罫線を挿入',
        'linkDialog.show': 'リンクダイアログを表示'
      },
      history: {
        undo: '元に戻す',
        redo: 'やり直す'
      },
      specialChar: {
        specialChar: '特殊文字',
        select: '特殊文字を選択'
      }
    }
  });
})(jQuery);
/******/ 	return __webpack_exports__;
/******/ })()
;
});
//# sourceMappingURL=summernote-zh-CN.js.map
