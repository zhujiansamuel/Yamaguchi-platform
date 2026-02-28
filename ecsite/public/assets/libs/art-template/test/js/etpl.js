/**
 * ETPL (Enterprise Template)
 * Copyright 2013 Baidu Inc. All rights reserved.
 * 
 * @file テンプレートエンジン
 * @author errorrik(errorrik@gmail.com)
 *         otakustay(otakustay@gmail.com)
 */

// 一部の正規表現はかなり長い，そのため一部制限を特別に緩和する
/* jshint maxdepth: 10, unused: false, white: false */

// HACK: 目に見える重複コードをfunctionやvarに抽出していないのはgzipサイズのためで、文句は受け付けませんfunctionとvarためですgzip size，文句ばかりに文句を言うな

(function (root) {
    /**
     * オブジェクトプロパティのコピー
     * 
     * @inner
     * @param {Object} target ターゲットオブジェクト
     * @param {Object} source ソースオブジェクト
     * @return {Object} ターゲットオブジェクトを返す
     */
    function extend( target, source ) {
        for ( var key in source ) {
            if ( source.hasOwnProperty( key ) ) {
                target[ key ] = source[ key ];
            }
        }

        return target;
    }

    /**
     * ついでにスタックを実装
     *
     * @inner
     * @constructor
     */
    function Stack() {
        this.raw = [];
        this.length = 0;
    }

    Stack.prototype = {
        /**
         * 要素をスタックに追加
         *
         * @param {*} elem 追加項目
         */
        push: function ( elem ) {
            this.raw[ this.length++ ] = elem;
        },

        /**
         * 先頭要素をポップ
         *
         * @return {*}
         */
        pop: function () {
            if ( this.length > 0 ) {
                var elem = this.raw[ --this.length ];
                this.raw.length = this.length;
                return elem;
            }
        },

        /**
         * 先頭要素を取得
         *
         * @return {*}
         */
        top: function () {
            return this.raw[ this.length - 1 ];
        },

        /**
         * 末尾要素を取得
         *
         * @return {*}
         */
        bottom: function () {
            return this.raw[ 0 ];
        },

        /**
         * 検索条件に基づいて要素を取得
         * 
         * @param {Function} condition 検索関数
         * @return {*}
         */
        find: function ( condition ) {
            var index = this.length;
            while ( index-- ) {
                var item = this.raw[ index ];
                if ( condition( item ) ) {
                    return item;
                }
            }
        }
    };

    /**
     * ユニークidの開始値
     * 
     * @inner
     * @type {number}
     */
    var guidIndex = 0x2B845;

    /**
     * ユニークIDを取得id，匿名ターゲット用targetまたはコンパイルコードの変数名生成用
     * 
     * @inner
     * @return {string}
     */
    function generateGUID() {
        return '___' + (guidIndex++);
    }

    /**
     * クラス間の継承関係を構築する
     * 
     * @inner
     * @param {Function} subClass サブクラス関数
     * @param {Function} superClass スーパークラス関数
     */
    function inherits( subClass, superClass ) {
        var F = new Function();
        F.prototype = superClass.prototype;
        subClass.prototype = new F();
        subClass.prototype.constructor = subClass;
        // エンジン内部での使用シーンはすべてinherits後，その後にサブクラスのprototypeメソッドを一つずつ記述するためprototypeメソッド
        // そのため，元のサブクラスのprototypeをprototypeキャッシュしてから一つずつコピーし直すことは考慮しない
    }

    /**
     * HTML Filter置換用文字実体のテーブル
     * 
     * @const
     * @inner
     * @type {Object}
     */
    var HTML_ENTITY = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };

    /**
     * HTML Filterの置換関数
     * 
     * @inner
     * @param {string} c 置換文字
     * @return {string}
     */
    function htmlFilterReplacer( c ) {
        return HTML_ENTITY[ c ];
    }

    /**
     * デフォルトfilter
     * 
     * @inner
     * @const
     * @type {Object}
     */
    var DEFAULT_FILTERS = {
        /**
         * HTMLエスケープfilter
         * 
         * @param {string} source 元の文字列
         * @return {string}
         */
        html: function ( source ) {
            return source.replace( /[&<>"']/g, htmlFilterReplacer );
        },

        /**
         * URLエンコードfilter
         * 
         * @param {string} source 元の文字列
         * @return {string}
         */
        url: encodeURIComponent,

        /**
         * 元の文字列filter，デフォルトでHTMLエスケープが有効な場合にHTML转义时获取元の文字列，エスケープを行わない
         * 
         * @param {string} source 元の文字列
         * @return {string}
         */
        raw: function ( source ) {
            return source;
        }
    };

    /**
     * 文字列リテラル化
     * 
     * @inner
     * @param {string} source リテラル化が必要な文字列
     * @return {string}
     */
    function stringLiteralize( source ) {
        return '"'
            + source
                .replace( /\x5C/g, '\\\\' )
                .replace( /"/g, '\\"' )
                .replace( /\x0A/g, '\\n' )
                .replace( /\x09/g, '\\t' )
                .replace( /\x0D/g, '\\r' )
                // .replace( /\x08/g, '\\b' )
                // .replace( /\x0C/g, '\\f' )
            + '"';
    }

    /**
     * 文字列フォーマット
     * 
     * @inner
     * @param {string} source ターゲットテンプレート文字列
     * @param {...string} replacements 文字列の置換項目集合
     * @return {string}
     */
    function stringFormat( source ) {
        var args = arguments;
        return source.replace( 
            /\{([0-9]+)\}/g,
            function ( match, index ) {
                return args[ index - 0 + 1 ];
            } );
    }

    /**
     * に使用するrender用の文字列変数宣言文
     * 
     * @inner
     * @const
     * @type {string}
     */
    var RENDER_STRING_DECLATION = 'var r="";';

    /**
     * に使用するrender用の文字列内容追加文（開始）
     * 
     * @inner
     * @const
     * @type {string}
     */
    var RENDER_STRING_ADD_START = 'r+=';

    /**
     * に使用するrender用の文字列内容追加文（終了）
     * 
     * @inner
     * @const
     * @type {string}
     */
    var RENDER_STRING_ADD_END = ';';

    /**
     * に使用するrender用の文字列内容返却文
     * 
     * @inner
     * @const
     * @type {string}
     */
    var RENDER_STRING_RETURN = 'return r;';

    // HACK: IE8-のときは，コンパイル後のrenderer使用join Arrayの戦略で文字列結合を行う
    if ( typeof navigator != 'undefined' 
        && /msie\s*([0-9]+)/i.test( navigator.userAgent )
        && RegExp.$1 - 0 < 8
    ) {
        RENDER_STRING_DECLATION = 'var r=[],ri=0;';
        RENDER_STRING_ADD_START = 'r[ri++]=';
        RENDER_STRING_RETURN = 'return r.join("");';
    }

    /**
     * アクセスする変数名をgetVariable呼び出しのコンパイル文に変換する
     * に使用するif、varなどのコマンドでコンパイルコードを生成する
     * 
     * @inner
     * @param {string} name アクセスする変数名
     * @return {string}
     */
    function toGetVariableLiteral( name ) {
        name = name.replace( /^\s*\*/, '' );
        return stringFormat(
            'gv({0},["{1}"])',
            stringLiteralize( name ),
            name.replace(
                    /\[['"]?([^'"]+)['"]?\]/g, 
                    function ( match, name ) {
                        return '.' + name;
                    }
                )
                .split( '.' )
                .join( '","' )
        );
    }

    /**
     * テキスト片から、特定の文字列で始まり終わるブロックを解析する
     * に使用する コマンド文字列：<!-- ... --> と 変数置換文字列：${...} の解析
     * 
     * @inner
     * @param {string} source 解析対象のテキスト
     * @param {string} open ブロック開始を含む
     * @param {string} close ブロック終了を含む
     * @param {boolean} greedy 貪欲マッチを行うかどうか
     * @param {function({string})} onInBlock ブロック内テキストの処理関数
     * @param {function({string})} onOutBlock ブロック外テキストの処理関数
     */
    function parseTextBlock( source, open, close, greedy, onInBlock, onOutBlock ) {
        var closeLen = close.length;
        var texts = source.split( open );
        var level = 0;
        var buf = [];

        for ( var i = 0, len = texts.length; i < len; i++ ) {
            var text = texts[ i ];

            if ( i ) {
                var openBegin = 1;
                level++;
                while ( 1 ) {
                    var closeIndex = text.indexOf( close );
                    if ( closeIndex < 0 ) {
                        buf.push( level > 1 && openBegin ? open : '', text );
                        break;
                    }

                    level = greedy ? level - 1 : 0;
                    buf.push( 
                        level > 0 && openBegin ? open : '',
                        text.slice( 0, closeIndex ),
                        level > 0 ? close : ''
                    );
                    text = text.slice( closeIndex + closeLen );
                    openBegin = 0;

                    if ( level === 0 ) {
                        break;
                    }
                }

                if ( level === 0 ) {
                    onInBlock( buf.join( '' ) );
                    onOutBlock( text );
                    buf = [];
                }
            }
            else {
                text && onOutBlock( text );
            }
        }

        if ( level > 0 && buf.length > 0 ) {
            onOutBlock( open );
            onOutBlock( buf.join( '' ) );
        }
    }

    /**
     * 変数アクセスおよび変数置換コードのコンパイル
     * 通常テキストまたはif、var、filterなどのコマンドでコンパイルコードを生成する
     * 
     * @inner
     * @param {string} source ソースコード
     * @param {Engine} engine エンジンインスタンス
     * @param {boolean} forText 出力テキストの変数置換かどうか
     * @return {string}
     */
    function compileVariable( source, engine, forText ) {
        var code = [];
        var options = engine.options;

        var toStringHead = '';
        var toStringFoot = '';
        var wrapHead = '';
        var wrapFoot = '';

        // デフォルトのfilter，タグLIB_LOADがforTextモード時に有効
        var defaultFilter;

        if ( forText ) {
            toStringHead = 'ts(';
            toStringFoot = ')';
            wrapHead = RENDER_STRING_ADD_START;
            wrapFoot = RENDER_STRING_ADD_END;
            defaultFilter = options.defaultFilter
        }

        parseTextBlock(
            source, options.variableOpen, options.variableClose, 1,

            function ( text ) {
                // デフォルトを追加filter
                // forText を処理する場合のみforTextのときは，デフォルトを追加する必要があるfilter
                // 処理if/var/useなどcommandのときは，デフォルトを追加する必要はないfilter
                if ( forText && text.indexOf( '|' ) < 0 && defaultFilter ) {
                    text += '|' + defaultFilter;
                }

                // variableCodeはgv呼び出し，その後ループで，外側をラップしてfilter的呼び出し
                // を形成するfilter["b"](filter["a"](gv(...)))
                // 
                // タグLIB_LOADがforTextモード，テキスト中の変数置換を処理する場合
                // に渡す値はfilter文字列形式である必要がある，そのためgv外側をさらに 1 層ラップする必要があるts呼び出し
                // を形成するfilter["b"](filter["a"](ts(gv(...))))
                // 
                // タグLIB_LOADがvariableNameで始まる*先頭が，無視しts呼び出し，元の値を直接渡すfilter
                var filterCharIndex = text.indexOf( '|' );
                var variableName = (filterCharIndex > 0
                    ? text.slice( 0, filterCharIndex )
                    : text).replace( /^\s+/, '' ).replace( /\s+$/, '' );
                var filterSource = filterCharIndex > 0
                    ? text.slice( filterCharIndex + 1 )
                    : '';

                var variableRawValue = variableName.indexOf( '*' ) === 0;
                var variableCode = [
                    variableRawValue ? '' : toStringHead,
                    toGetVariableLiteral( variableName ),
                    variableRawValue ? '' : toStringFoot
                ];

                if ( filterSource ) {
                    filterSource = compileVariable( filterSource, engine );
                    var filterSegs = filterSource.split( '|' );
                    for ( var i = 0, len = filterSegs.length; i < len; i++ ) {
                        var seg = filterSegs[ i ];

                        if ( /^\s*([a-z0-9_-]+)(\((.*)\))?\s*$/i.test( seg ) ) {
                            variableCode.unshift( 'fs["' + RegExp.$1 + '"](' );

                            if ( RegExp.$3 ) {
                                variableCode.push( 
                                    ',', 
                                    RegExp.$3
                                );
                            }

                            variableCode.push( ')' );
                        }
                    }
                }

                code.push(
                    wrapHead,
                    variableCode.join( '' ),
                    wrapFoot
                );
            },

            function ( text ) { 
                code.push( 
                    wrapHead, 
                    forText ? stringLiteralize( text ) : text, 
                    wrapFoot
                );
            }
        );

        return code.join( '' );
    }

    /**
     * テキストノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value テキストノードの内容テキスト
     * @param {Engine} engine エンジンインスタンス
     */
    function TextNode( value, engine ) {
        this.value = value;
        this.engine = engine;
    }
    
    TextNode.prototype = {
        /**
         * 取得renderer bodyの生成コード
         * 
         * @return {string}
         */
        getRendererBody: function () {
            var value = this.value;
            var options = this.engine.options;

            if ( !value || ( options.strip && /^\s*$/.test( value ) ) ) {
                return '';
            }

            return compileVariable( value, this.engine, 1 );
        },

        /**
         * 内容を取得
         * 
         * @return {string}
         */
        getContent: function () {
            return this.value;
        }
    };

    /**
     * コマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function Command( value, engine ) {
        this.value = value;
        this.engine = engine;
        this.children = [];
    }

    Command.prototype = {
        /**
         * 子ノードを追加
         * 
         * @param {TextNode|Command} node 子ノード
         */
        addChild: function ( node ) {
            this.children.push( node );
        },

        /**
         * ノードopen，解析開始
         * 
         * @param {Object} context 構文解析コンテキストオブジェクト
         */
        open: function ( context ) {
            var parent = context.stack.top();
            this.parent = parent;
            parent && parent.addChild( this );
            context.stack.push( this );
        },

        /**
         * ノードクローズ，解析終了
         * 
         * @param {Object} context 構文解析コンテキストオブジェクト
         */
        close: function ( context ) {
            while (context.stack.pop().constructor !== this.constructor) {}
        },

        /**
         * テキストノードを追加
         * 
         * @param {TextNode} node ノード
         */
        addTextNode: function ( node ) {
            this.addChild( node );
        },

        /**
         * 取得renderer bodyの生成コード
         * 
         * @return {string}
         */
        getRendererBody: function () {
            var buf = [];
            var children = this.children;
            for ( var i = 0; i < children.length; i++ ) {
                buf.push( children[ i ].getRendererBody() );
            }

            return buf.join( '' );
        }
    };

    /**
     * コマンドの自動クローズ
     * 
     * @inner
     * @param {Object} context 構文解析コンテキストオブジェクト
     * @param {Function=} CommandType 自己クローズノードタイプ
     */
    function autoCloseCommand( context, CommandType ) {
        var stack = context.stack;
        var closeEnd = CommandType 
            ? stack.find( function ( item ) {
                return item instanceof CommandType;
            } ) 
            : stack.bottom();

        if ( closeEnd ) {
            var node;

            do {
                node = stack.top();

                // ノードオブジェクトにautoCloseメソッド
                // そのノードは自動クローズ非対応とみなす，エラーをスローする必要がある
                // forなどのノードは自動クローズに対応していない
                if ( !node.autoClose ) {
                    throw new Error( node.type + ' must be closed manually: ' + node.value );
                }
                node.autoClose( context );
            } while ( node !== closeEnd );
        }

        return closeEnd;
    }

    /**
     * renderer body開始コードセクション
     * 
     * @inner
     * @const
     * @type {string}
     */
    var RENDERER_BODY_START = ''
        + 'data=data||{};'
        + 'var v={},fs=engine.filters,hg=typeof data.get=="function",'
        + 'gv=function(n,ps){'
        +     'var p=ps[0],d=v[p];'
        +     'if(d==null){'
        +         'if(hg){return data.get(n);}'
        +         'd=data[p];'
        +     '}'
        +     'for(var i=1,l=ps.length;i<l;i++)if(d!=null)d = d[ps[i]];'
        +     'return d;'
        + '},'
        + 'ts=function(s){'
        +     'if(typeof s==="string"){return s;}'
        +     'if(s==null){s="";}'
        +     'return ""+s;'
        + '};'
    ;
    // v: variables
    // fs: filters
    // gv: getVariable
    // ts: toString
    // n: name
    // ps: properties
    // hg: hasGetter

    /**
     * Targetコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function TargetCommand( value, engine ) {
        if ( !/^\s*([a-z0-9_-]+)\s*(\(\s*master\s*=\s*([a-z0-9_-]+)\s*\))?\s*/i.test( value ) ) {
            throw new Error( 'Invalid ' + this.type + ' syntax: ' + value );
        }
        
        this.master = RegExp.$3;
        this.name = RegExp.$1;
        Command.call( this, value, engine );
        this.contents = {};
    }

    // 作成Targetコマンドノードの継承関係
    inherits( TargetCommand, Command );

    /**
     * Masterコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function MasterCommand( value, engine ) {
        if ( !/^\s*([a-z0-9_-]+)\s*(\(\s*master\s*=\s*([a-z0-9_-]+)\s*\))?\s*/i.test( value ) ) {
            throw new Error( 'Invalid ' + this.type + ' syntax: ' + value );
        }
        
        this.master = RegExp.$3;
        this.name = RegExp.$1;
        Command.call( this, value, engine );
        this.contents = {};
    }

    // 作成Masterコマンドノードの継承関係
    inherits( MasterCommand, Command );

    /**
     * Contentコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function ContentCommand( value, engine ) {
        if ( !/^\s*([a-z0-9_-]+)\s*$/i.test( value ) ) {
            throw new Error( 'Invalid ' + this.type + ' syntax: ' + value );
        }

        this.name = RegExp.$1;
        Command.call( this, value, engine );
    }

    // 作成Contentコマンドノードの継承関係
    inherits( ContentCommand, Command );

    /**
     * ContentPlaceHolderコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function ContentPlaceHolderCommand( value, engine ) {
        if ( !/^\s*([a-z0-9_-]+)\s*$/i.test( value ) ) {
            throw new Error( 'Invalid ' + this.type + ' syntax: ' + value );
        }

        this.name = RegExp.$1;
        Command.call( this, value, engine );
    }

    // 作成ContentPlaceHolderコマンドノードの継承関係
    inherits( ContentPlaceHolderCommand, Command );
    
    /**
     * Importコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function ImportCommand( value, engine ) {
        if ( !/^\s*([a-z0-9_-]+)\s*$/i.test( value ) ) {
            throw new Error( 'Invalid ' + this.type + ' syntax: ' + value );
        }

        this.name = RegExp.$1;
        Command.call( this, value, engine );
    }

    // 作成Importコマンドノードの継承関係
    inherits( ImportCommand, Command );

    /**
     * Varコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function VarCommand( value, engine ) {
        if ( !/^\s*([a-z0-9_]+)\s*=([\s\S]*)$/i.test( value ) ) {
            throw new Error( 'Invalid ' + this.type + ' syntax: ' + value );
        }

        this.name = RegExp.$1;
        this.expr = RegExp.$2;
        Command.call( this, value, engine );
    }

    // 作成Varコマンドノードの継承関係
    inherits( VarCommand, Command );

    /**
     * filterコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function FilterCommand( value, engine ) {
        if ( !/^\s*([a-z0-9_-]+)\s*(\(([\s\S]*)\))?\s*$/i.test( value ) ) {
            throw new Error( 'Invalid ' + this.type + ' syntax: ' + value );
        }

        this.name = RegExp.$1;
        this.args = RegExp.$3;
        Command.call( this, value, engine );
    }

    // 作成filterコマンドノードの継承関係
    inherits( FilterCommand, Command );

    /**
     * Useコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function UseCommand( value, engine ) {
        if ( !/^\s*([a-z0-9_-]+)\s*(\(([\s\S]*)\))?\s*$/i.test( value ) ) {
            throw new Error( 'Invalid ' + this.type + ' syntax: ' + value );
        }

        this.name = RegExp.$1;
        this.args = RegExp.$3;
        Command.call( this, value, engine );
    }

    // 作成Useコマンドノードの継承関係
    inherits( UseCommand, Command );

    /**
     * forコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function ForCommand( value, engine ) {
        if ( !/^\s*(\$\{[\s\S]+\})\s+as\s+\$\{([0-9a-z_]+)\}\s*(,\s*\$\{([0-9a-z_]+)\})?\s*$/i.test( value ) ) {
            throw new Error( 'Invalid ' + this.type + ' syntax: ' + value );
        }
        
        this.list = RegExp.$1;
        this.item = RegExp.$2;
        this.index = RegExp.$4;
        Command.call( this, value, engine );
    }

    // 作成forコマンドノードの継承関係
    inherits( ForCommand, Command );
    
    /**
     * ifコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function IfCommand( value, engine ) {
        Command.call( this, value, engine );
    }

    // 作成ifコマンドノードの継承関係
    inherits( IfCommand, Command );

    /**
     * elifコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function ElifCommand( value, engine ) {
        IfCommand.call( this, value, engine );
    }

    // 作成elifコマンドノードの継承関係
    inherits( ElifCommand, IfCommand );

    /**
     * elseコマンドノードクラス
     * 
     * @inner
     * @constructor
     * @param {string} value コマンドノードのvalue
     * @param {Engine} engine エンジンインスタンス
     */
    function ElseCommand( value, engine ) {
        Command.call( this, value, engine );
    }

    // 作成elseコマンドノードの継承関係
    inherits( ElseCommand, Command ); 
    
    /**
     * TargetとMasterのノード状態
     * 
     * @inner
     */
    var TMNodeState = {
        READING: 1,
        READED: 2,
        APPLIED: 3,
        READY: 4
    };

    /**
     * ノードクローズ，解析終了
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    MasterCommand.prototype.close =

    /**
     * ノードクローズ，解析終了。自己クローズ時に呼び出される
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    MasterCommand.prototype.autoClose = 

    /**
     * ノードクローズ，解析終了
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    TargetCommand.prototype.close =

    /**
     * ノードクローズ，解析終了。自己クローズ時に呼び出される
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    TargetCommand.prototype.autoClose = function ( context ) {
        Command.prototype.close.call( this, context );
        this.state = this.master ? TMNodeState.READED : TMNodeState.APPLIED;
        context.targetOrMaster = null;
    };

    /**
     * 継承しているマスタを適用する，マスタの適用に成功したかどうかを返す
     * 
     * @return {boolean}
     */
    TargetCommand.prototype.applyMaster = 

    /**
     * 継承しているマスタを適用する，マスタの適用に成功したかどうかを返す
     * 
     * @return {boolean}
     */
    MasterCommand.prototype.applyMaster = function () {
        if ( this.state >= TMNodeState.APPLIED ) {
            return 1;
        }

        var masterNode = this.engine.masters[ this.master ];
        if ( masterNode && masterNode.applyMaster() ) {
            this.children = [];

            for ( var i = 0, len = masterNode.children.length; i < len; i++ ) {
                var child = masterNode.children[ i ];

                if ( child instanceof ContentPlaceHolderCommand ) {
                    this.children.push.apply( 
                        this.children, 
                        (this.contents[ child.name ] || child).children
                    );
                }
                else {
                    this.children.push( child );
                }
            }

            this.state = TMNodeState.APPLIED;
            return 1;
        }
    };

    /**
     * 判定targetかどうかready
     * 包括かどうか成功应用母版，およびimportとuse文に依存するtargetかどうかready
     * 
     * @return {boolean}
     */
    TargetCommand.prototype.isReady = function () {
        if ( this.state >= TMNodeState.READY ) {
            return 1;
        }

        var engine = this.engine;
        var readyState = 1;

        /**
         * ノードのreadyステータス
         * 
         * @inner
         * @param {Command|TextNode} node 対象ノード
         */
        function checkReadyState( node ) {
            for ( var i = 0, len = node.children.length; i < len; i++ ) {
                var child = node.children[ i ];
                if ( child instanceof ImportCommand ) {
                    var target = engine.targets[ child.name ];
                    readyState = readyState 
                        && target && target.isReady( engine );
                }
                else if ( child instanceof Command ) {
                    checkReadyState( child );
                }
            }
        }

        if ( this.applyMaster() ) {
            checkReadyState( this );
            readyState && (this.state = TMNodeState.READY);
            return readyState;
        }
    };

    /**
     * 取得targetのrenderer関数
     * 
     * @return {function(Object):string}
     */
    TargetCommand.prototype.getRenderer = function () {
        if ( this.renderer ) {
            return this.renderer;
        }

        if ( this.isReady() ) {
            // console.log( this.name + ' ------------------' );
            // console.log(RENDERER_BODY_START +RENDER_STRING_DECLATION
            //     + this.getRendererBody() 
            //     + RENDER_STRING_RETURN);

            var realRenderer = new Function( 
                'data', 'engine',
                [
                    RENDERER_BODY_START,
                    RENDER_STRING_DECLATION,
                    this.getRendererBody(),
                    RENDER_STRING_RETURN
                ].join( '\n' )
            );

            var engine = this.engine;
            this.renderer = function ( data ) {
                return realRenderer( data, engine );
            };

            return this.renderer;
        }

        return null;
    };

    /**
     * 内容を取得
     * 
     * @return {string}
     */
    TargetCommand.prototype.getContent = function () {
        if ( this.isReady() ) {
            var buf = [];
            var children = this.children;
            for ( var i = 0; i < children.length; i++ ) {
                buf.push( children[ i ].getContent() );
            }

            return buf.join( '' );
        }

        return '';
    };

    /**
     * をtargetまたはmasterノードオブジェクトを構文解析コンテキストに追加する
     * 
     * @inner
     * @param {TargetCommand|MasterCommand} targetOrMaster targetまたはmasterノードオブジェクト
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    function addTargetOrMasterToContext( targetOrMaster, context ) {
        context.targetOrMaster = targetOrMaster;

        var engine = context.engine;
        var name = targetOrMaster.name;
        var isTarget = targetOrMaster instanceof TargetCommand;
        var prop = isTarget ? 'targets' : 'masters';

        if ( engine[ prop ][ name ] ) {
            switch ( engine.options.namingConflict ) {
                case 'override':
                    engine[ prop ][ name ] = targetOrMaster;
                    isTarget && context.targets.push( name );
                case 'ignore':
                    break;
                default:
                    throw new Error( ( isTarget ? 'Target' :'Master' ) 
                        + ' is exists: ' + name );
            }
        }
        else {
            engine[ prop ][ name ] = targetOrMaster;
            isTarget && context.targets.push( name );
        }
    }

    /**
     * targetノードopen，解析開始
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    TargetCommand.prototype.open = 

    /**
     * masterノードopen，解析開始
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    MasterCommand.prototype.open = function ( context ) {
        autoCloseCommand( context );
        Command.prototype.open.call( this, context );
        this.state = TMNodeState.READING;
        addTargetOrMasterToContext( this, context );
    };

    /**
     * Importノードopen，解析開始
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ImportCommand.prototype.open = 

    /**
     * Varノードopen，解析開始
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    VarCommand.prototype.open = 

    /**
     * Useノードopen，解析開始
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    UseCommand.prototype.open = function ( context ) {
        var parent = context.stack.top();
        this.parent = parent;
        parent.addChild( this );
    };


    /**
     * ノードopen前の処理アクション：ノード不在target内にない場合，匿名のを自動作成するtarget
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    UseCommand.prototype.beforeOpen = 

    /**
     * ノードopen前の処理アクション：ノード不在target内にない場合，匿名のを自動作成するtarget
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ImportCommand.prototype.beforeOpen = 

    /**
     * ノードopen前の処理アクション：ノード不在target内にない場合，匿名のを自動作成するtarget
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    VarCommand.prototype.beforeOpen = 

    /**
     * ノードopen前の処理アクション：ノード不在target内にない場合，匿名のを自動作成するtarget
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ForCommand.prototype.beforeOpen = 

    /**
     * ノードopen前の処理アクション：ノード不在target内にない場合，匿名のを自動作成するtarget
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    FilterCommand.prototype.beforeOpen = 

    /**
     * ノードopen前の処理アクション：ノード不在target内にない場合，匿名のを自動作成するtarget
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    IfCommand.prototype.beforeOpen = 

    /**
     * テキストノードが解析コンテキストに追加される前の処理アクション：ノードがtarget内にない場合，匿名のを自動作成するtarget
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    TextNode.prototype.beforeAdd =  function ( context ) {
        if ( context.stack.bottom() ) {
            return;
        }

        var target = new TargetCommand( generateGUID(), context.engine );
        target.open( context );
    };
    
    /**
     * ノード解析完了
     * 〜のためuseノードはクローズ不要，処理時にスタックに積まれない，そのためcloseを空の関数にする
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    UseCommand.prototype.close = 

    /**
     * ノード解析完了
     * 〜のためimportノードはクローズ不要，処理時にスタックに積まれない，そのためcloseを空の関数にする
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */ 
    ImportCommand.prototype.close = 

    /**
     * ノード解析完了
     * 〜のためelseノードはクローズ不要，処理時にスタックに積まれない，クローズは〜によって行われるif担当する。そのためcloseを空の関数にする
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ElseCommand.prototype.close = 

    /**
     * ノード解析完了
     * 〜のためvarノードはクローズ不要，処理時にスタックに積まれない，そのためcloseを空の関数にする
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    VarCommand.prototype.close = function () {};

    /**
     * 内容を取得
     * 
     * @return {string}
     */
    ImportCommand.prototype.getContent = function () {
        var target = this.engine.targets[ this.name ];
        return target.getContent();
    };
    
    /**
     * 取得renderer bodyの生成コード
     * 
     * @return {string}
     */
    ImportCommand.prototype.getRendererBody = function () {
        var target = this.engine.targets[ this.name ];
        return target.getRendererBody();
    };

    /**
     * 取得renderer bodyの生成コード
     * 
     * @return {string}
     */
    UseCommand.prototype.getRendererBody = function () {
        return stringFormat(
            '{0}engine.render({2},{{3}}){1}',
            RENDER_STRING_ADD_START,
            RENDER_STRING_ADD_END,
            stringLiteralize( this.name ),
            compileVariable( this.args, this.engine ).replace( 
                /(^|,)\s*([a-z0-9_]+)\s*=/ig,
                function ( match, start, argName ) {
                    return (start || '') + stringLiteralize( argName ) + ':';
                }
            )
        );
    };
    
    /**
     * 取得renderer bodyの生成コード
     * 
     * @return {string}
     */
    VarCommand.prototype.getRendererBody = function () {
        if ( this.expr ) {
            return stringFormat( 
                'v[{0}]={1};',
                stringLiteralize( this.name ),
                compileVariable( this.expr, this.engine )
            );
        }

        return '';
    };

    /**
     * 取得renderer bodyの生成コード
     * 
     * @return {string}
     */
    IfCommand.prototype.getRendererBody = function () {
        var rendererBody = stringFormat(
            'if({0}){{1}}',
            compileVariable( this.value, this.engine ),
            Command.prototype.getRendererBody.call( this )
        );

        var elseCommand = this[ 'else' ];
        if ( elseCommand ) {
            return [
                rendererBody,
                stringFormat( 
                    'else{{0}}',
                    elseCommand.getRendererBody()
                )
            ].join( '' );
        }

        return rendererBody;
    };

    /**
     * 取得renderer bodyの生成コード
     * 
     * @return {string}
     */
    ForCommand.prototype.getRendererBody = function () {
        return stringFormat(
            ''
            + 'var {0}={1};'
            + 'if({0} instanceof Array)'
            +     'for (var {4}=0,{5}={0}.length;{4}<{5};{4}++){v[{2}]={4};v[{3}]={0}[{4}];{6}}'
            + 'else if(typeof {0}==="object")'
            +     'for(var {4} in {0}){v[{2}]={4};v[{3}]={0}[{4}];{6}}',
            generateGUID(),
            compileVariable( this.list, this.engine ),
            stringLiteralize( this.index || generateGUID() ),
            stringLiteralize( this.item ),
            generateGUID(),
            generateGUID(),
            Command.prototype.getRendererBody.call( this )
        );
    };

    /**
     * 取得renderer bodyの生成コード
     * 
     * @return {string}
     */
    FilterCommand.prototype.getRendererBody = function () {
        var args = this.args;
        return stringFormat(
            '{2}fs[{5}]((function(){{0}{4}{1}})(){6}){3}',
            RENDER_STRING_DECLATION,
            RENDER_STRING_RETURN,
            RENDER_STRING_ADD_START,
            RENDER_STRING_ADD_END,
            Command.prototype.getRendererBody.call( this ),
            stringLiteralize( this.name ),
            args ? ',' + compileVariable( args, this.engine ) : ''
        );
    };

    /**
     * contentノードopen，解析開始
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ContentCommand.prototype.open = function ( context ) {
        autoCloseCommand( context, ContentCommand );
        Command.prototype.open.call( this, context );
        context.targetOrMaster.contents[ this.name ] = this;
    };
    
    /**
     * contentノードopen，解析開始
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ContentPlaceHolderCommand.prototype.open = function ( context ) {
        autoCloseCommand( context, ContentPlaceHolderCommand );
        Command.prototype.open.call( this, context );
    };

    /**
     * ノードが自動的にクローズされる，解析終了
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ContentCommand.prototype.autoClose = 

    /**
     * ノードが自動的にクローズされる，解析終了
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    IfCommand.prototype.autoClose = Command.prototype.close;

    /**
     * ノードが自動的にクローズされる，解析終了
     * contentplaceholderの自動終了ロジックは，開始位置の直後で終了する
     * そのため，その自動終了時にchildren所属するに割り当てるべきであるparent，すなわちmaster
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ContentPlaceHolderCommand.prototype.autoClose = function ( context ) {
        var parentChildren = this.parent.children;
        parentChildren.push.apply( parentChildren, this.children );
        this.children.length = 0;
        this.close( context );
    };
    
    /**
     * 子ノードを追加
     * 
     * @param {TextNode|Command} node 子ノード
     */
    IfCommand.prototype.addChild = function ( node ) {
        var elseCommand = this[ 'else' ];
        ( elseCommand 
            ? elseCommand.children 
            : this.children
        ).push( node );
    };

    /**
     * elifノードopen，解析開始
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ElifCommand.prototype.open = function ( context ) {
        var elseCommand = new ElseCommand();
        elseCommand.open( context );

        var ifCommand = autoCloseCommand( context, IfCommand );
        ifCommand.addChild( this );
        context.stack.push( this );
    };

    /**
     * elseノードopen，解析開始
     * 
     * @param {Object} context 構文解析コンテキストオブジェクト
     */
    ElseCommand.prototype.open = function ( context ) {
        var ifCommand = autoCloseCommand( context, IfCommand );
        
        ifCommand[ 'else' ] = this;
        context.stack.push( ifCommand );
    };
    
    /**
     * コマンドタイプの集合
     * 
     * @type {Object}
     */
    var commandTypes = {};

    /**
     * コマンドタイプを追加
     * 
     * @inner
     * @param {string} name コマンド名
     * @param {Function} Type コマンド処理に使用されるクラス
     */
    function addCommandType( name, Type ) {
        commandTypes[ name ] = Type;
        Type.prototype.type = name;
    }

    addCommandType( 'target', TargetCommand );
    addCommandType( 'master', MasterCommand );
    addCommandType( 'content', ContentCommand );
    addCommandType( 'contentplaceholder', ContentPlaceHolderCommand );
    addCommandType( 'import', ImportCommand );
    addCommandType( 'use', UseCommand );
    addCommandType( 'var', VarCommand );
    addCommandType( 'for', ForCommand );
    addCommandType( 'if', IfCommand );
    addCommandType( 'elif', ElifCommand );
    addCommandType( 'else', ElseCommand );
    addCommandType( 'filter', FilterCommand );
    
    
    /**
     * etpletpl エンジンクラス
     * 
     * @constructor
     * @param {Object=} options エンジンのパラメーター
     * @param {string=} options.commandOpen コマンド構文の開始文字列
     * @param {string=} options.commandClose コマンド構文の終了文字列
     * @param {string=} options.defaultFilter デフォルトの変数置換に使用するfilter
     * @param {boolean=} options.strip コマンドタグ前後の空白文字を削除するかどうか
     * @param {string=} options.namingConflict targetまたはmaster名前が衝突した場合の処理ポリシー
     */
    function Engine( options ) {
        this.options = {
            commandOpen: '<!--',
            commandClose: '-->',
            variableOpen: '${',
            variableClose: '}',
            defaultFilter: 'html'
        };

        this.config( options );
        this.masters = {};
        this.targets = {};
        this.filters = extend({}, DEFAULT_FILTERS);
    }

    /**
     * エンジンパラメータを設定する，設定したパラメータは既存のパラメータにマージされる
     * 
     * @param {Object} options パラメータオブジェクト
     * @param {string=} options.commandOpen コマンド構文の開始文字列
     * @param {string=} options.commandClose コマンド構文の終了文字列
     * @param {string=} options.defaultFilter デフォルトの変数置換に使用するfilter
     * @param {boolean=} options.strip コマンドタグ前後の空白文字を削除するかどうか
     * @param {string=} options.namingConflict targetまたはmaster名前が衝突した場合の処理ポリシー
     */
    Engine.prototype.config =  function ( options ) {
        extend( this.options, options );
    };

    /**
     * テンプレートを解析してコンパイルする，最初のを返すtargetコンパイル後のrenderer関数。
     * 
     * @param {string} source テンプレートソースコード
     * @return {function(Object):string}
     */
    Engine.prototype.compile = 

    /**
     * テンプレートを解析してコンパイルする，最初のを返すtargetコンパイル後のrenderer関数。
     * このメソッドは旧テンプレートエンジンとの互換性のために存在する
     * 
     * @param {string} source テンプレートソースコード
     * @return {function(Object):string}
     */
    Engine.prototype.parse = function ( source ) {
        if ( source ) {
            var targetNames = parseSource( source, this );
            if ( targetNames.length ) {
                return this.targets[ targetNames[ 0 ] ].getRenderer();
            }
        }

        return new Function('return ""');
    };
    
    /**
     * に基づいてtarget名前に基づいてコンパイル済みのを取得するrenderer関数
     * 
     * @param {string} name target名称
     * @return {function(Object):string}
     */
    Engine.prototype.getRenderer = function ( name ) {
        var target = this.targets[ name ];
        if ( target ) {
            return target.getRenderer();
        }
    };

    /**
     * に基づいてtarget名前でテンプレート内容を取得
     * 
     * @param {string} name target名称
     * @return {string}
     */
    Engine.prototype.get = function ( name ) {
        var target = this.targets[ name ];
        if ( target ) {
            return target.getContent();
        }

        return '';
    };

    /**
     * テンプレートをレンダリング実行，レンダリング後の文字列を返す。
     * 
     * @param {string} name target名称
     * @param {Object=} data テンプレートデータ。
     *      ～でもよいplain object，
     *      また、～を持つ {string}get({string}name) メソッドを持つオブジェクトでもよい
     * @return {string}
     */
    Engine.prototype.render = function ( name, data ) {
        var renderer = this.getRenderer( name );
        if ( renderer ) {
            return renderer( data );
        }

        return '';
    };

    /**
     * フィルタを追加
     * 
     * @param {string} name フィルタ名
     * @param {Function} filter フィルタ関数
     */
    Engine.prototype.addFilter = function ( name, filter ) {
        if ( typeof filter == 'function' ) {
            this.filters[ name ] = filter;
        }
    };

    /**
     * ソースコードを解析
     * 
     * @inner
     * @param {string} source テンプレートソースコード
     * @param {Engine} engine エンジンインスタンス
     * @return {Array} target名前一覧
     */
    function parseSource( source, engine ) {
        var commandOpen = engine.options.commandOpen;
        var commandClose = engine.options.commandClose;

        var stack = new Stack();
        var analyseContext = {
            engine: engine,
            targets: [],
            stack: stack
        };

        // textノード内容バッファ，複数のテキストを結合するためのtext
        var textBuf = [];

        /**
         * バッファ内のtextノード内容を書き込む
         *
         * @inner
         */
        function flushTextBuf() {
            if ( textBuf.length > 0 ) {
                var text = textBuf.join( '' );
                var textNode = new TextNode( text, engine );
                textNode.beforeAdd( analyseContext );

                stack.top().addTextNode( textNode );
                textBuf = [];

                if ( engine.options.strip 
                    && analyseContext.current instanceof Command 
                ) {
                    textNode.value = text.replace( /^[\x20\t\r]*\n/, '' );
                }
                analyseContext.current = textNode;
            }
        }

        var NodeType;

        /**
         * ノードが～かどうかを判定NodeTypeタイプのインスタンスかどうか
         * ～で使用されstack中find提供するfilter
         * 
         * @inner
         * @param {Command} node 対象ノード
         * @return {boolean}
         */
        function isInstanceofNodeType( node ) {
            return node instanceof NodeType;
        }

        parseTextBlock(
            source, commandOpen, commandClose, 0,

            function ( text ) { // <!--...-->内テキストの処理関数
                var match = /^\s*(\/)?([a-z]+)\s*(:([\s\S]*))?$/.exec( text );

                // ルールに合致しcommandルール，かつ対応するCommandクラス，であれば、有効で意味のあるCommand
                // それ以外の場合，を持たないcommand意味を持たない通常テキスト
                if ( match 
                    && ( NodeType = commandTypes[ match[2].toLowerCase() ] )
                    && typeof NodeType == 'function'
                ) {
                    // まずバッファ内のtextノード内容を書き込む
                    flushTextBuf(); 

                    var currentNode = analyseContext.current;
                    if ( engine.options.strip && currentNode instanceof TextNode ) {
                        currentNode.value = currentNode.value
                            .replace( /\r?\n[\x20\t]*$/, '\n' );
                    }

                    if ( match[1] ) {
                        currentNode = stack.find( isInstanceofNodeType );
                        currentNode && currentNode.close( analyseContext );
                    }
                    else {
                        currentNode = new NodeType( match[4], engine );
                        if ( typeof currentNode.beforeOpen == 'function' ) {
                            currentNode.beforeOpen( analyseContext );
                        }
                        currentNode.open( analyseContext );
                    }

                    analyseContext.current = currentNode;
                }
                else if ( !/^\s*\/\//.test( text ) ) {
                    // テンプレートコメントでない場合，通常テキストとして扱い，バッファに書き込む
                    textBuf.push( commandOpen, text, commandClose );
                }

                NodeType = null;
            },

            function ( text ) { // <!--...-->以外は，通常テキストの処理関数
                // 通常テキストをそのままバッファに書き込む
                textBuf.push( text );
            }
        );


        flushTextBuf(); // バッファ内のtextノード内容を書き込む
        autoCloseCommand( analyseContext );

        return analyseContext.targets;
    }

    var etpl = new Engine();
    etpl.Engine = Engine;
    
    if ( typeof exports == 'object' && typeof module == 'object' ) {
        // For CommonJS
        exports = module.exports = etpl;
    }
    else if ( typeof define == 'function' && define.amd ) {
        // For AMD
        define( etpl );
    }
    else {
        // For <script src="..."
        root.etpl = etpl;
    }
})(this);
