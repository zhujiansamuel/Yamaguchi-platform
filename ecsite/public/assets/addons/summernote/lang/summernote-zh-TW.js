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
    'zh-TW': {
      font: {
        bold: '太字',
        italic: '斜体',
        underline: '下線',
        clear: '書式をクリア',
        height: '行間',
        name: 'フォント',
        strikethrough: '取り消し線',
        subscript: '下付き',
        superscript: '上付き',
        size: 'フォントサイズ'
      },
      image: {
        image: '画像',
        insert: '画像を挿入',
        resizeFull: '拡大／縮小100%',
        resizeHalf: '拡大／縮小 50%',
        resizeQuarter: '拡大／縮小 25%',
        floatLeft: '左に回り込み',
        floatRight: '右に回り込み',
        floatNone: '回り込みを解除',
        shapeRounded: '形状: 角丸',
        shapeCircle: '形状: 丸型',
        shapeThumbnail: '形状: サムネイル',
        shapeNone: '形状: なし',
        dragImageHere: '画像をここにドラッグしてください',
        dropImage: 'Drop image or Text',
        selectFromFiles: 'ローカルからアップロード',
        maximumFileSize: '最大ファイルサイズ',
        maximumFileSizeError: 'ファイルサイズが最大値を超えています。',
        url: '画像 URL',
        remove: '画像を削除',
        original: 'Original'
      },
      video: {
        video: '動画',
        videoLink: '動画リンク',
        insert: '動画を挿入',
        url: '動画 URL',
        providers: '(動画 URL)'
      },
      link: {
        link: 'リンク',
        insert: 'リンクを挿入',
        unlink: 'リンクを解除',
        edit: 'リンクを編集',
        textToDisplay: '表示テキスト',
        url: 'リンク URL',
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
        insert: '水平線'
      },
      style: {
        style: 'スタイル',
        p: '標準',
        blockquote: '引用ブロック',
        pre: 'コードブロック',
        h1: '見出し 1',
        h2: '見出し 2',
        h3: '見出し 3',
        h4: '見出し 4',
        h5: '見出し 5',
        h6: '見出し 6'
      },
      lists: {
        unordered: '箇条書き',
        ordered: '番号付きリスト'
      },
      options: {
        help: 'ヘルプ',
        fullscreen: '全画面',
        codeview: 'ソースコード'
      },
      paragraph: {
        paragraph: '段落',
        outdent: 'インデントを減らす',
        indent: 'インデントを増やす',
        left: '右揃え',
        center: '中央揃え',
        right: '右揃え',
        justify: '両端揃え'
      },
      color: {
        recent: '文字色',
        more: 'その他',
        background: '背景',
        foreground: 'フォント',
        transparent: '透明',
        setTransparent: '透明',
        reset: 'リセット',
        resetToDefault: 'デフォルト'
      },
      shortcut: {
        shortcuts: 'ショートカットキー',
        close: '閉じる',
        textFormatting: '文字書式',
        action: '操作',
        paragraphFormatting: '段落書式',
        documentStyle: 'ドキュメントスタイル',
        extraKeys: '追加キー'
      },
      help: {
        'insertParagraph': 'Insert Paragraph',
        'undo': 'Undoes the last command',
        'redo': 'Redoes the last command',
        'tab': 'Tab',
        'untab': 'Untab',
        'bold': 'Set a bold style',
        'italic': 'Set a italic style',
        'underline': 'Set a underline style',
        'strikethrough': 'Set a strikethrough style',
        'removeFormat': 'Clean a style',
        'justifyLeft': 'Set left align',
        'justifyCenter': 'Set center align',
        'justifyRight': 'Set right align',
        'justifyFull': 'Set full align',
        'insertUnorderedList': 'Toggle unordered list',
        'insertOrderedList': 'Toggle ordered list',
        'outdent': 'Outdent on current paragraph',
        'indent': 'Indent on current paragraph',
        'formatPara': 'Change current block\'s format as a paragraph(P tag)',
        'formatH1': 'Change current block\'s format as H1',
        'formatH2': 'Change current block\'s format as H2',
        'formatH3': 'Change current block\'s format as H3',
        'formatH4': 'Change current block\'s format as H4',
        'formatH5': 'Change current block\'s format as H5',
        'formatH6': 'Change current block\'s format as H6',
        'insertHorizontalRule': 'Insert horizontal rule',
        'linkDialog.show': 'Show Link Dialog'
      },
      history: {
        undo: '元に戻す',
        redo: 'やり直し'
      },
      specialChar: {
        specialChar: 'SPECIAL CHARACTERS',
        select: 'Select Special characters'
      }
    }
  });
})(jQuery);
/******/ 	return __webpack_exports__;
/******/ })()
;
});
//# sourceMappingURL=summernote-zh-TW.js.map
