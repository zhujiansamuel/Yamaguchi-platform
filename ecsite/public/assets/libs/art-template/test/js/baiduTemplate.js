/**
 * baiduTemplateシンプルで使いやすいJavascriptテンプレートエンジン 1.0.6 バージョン
 * http://baidufe.github.com/BaiduTemplate
 * オープンソースライセンス：BSD License
 * ブラウザ環境で占有する名前空間 baidu.template ，nodejs環境では直接インストール npm install baidutemplate
 * @param str{String} domノードID，またはテンプレートstring
 * @param data{Object} レンダリング対象のjsonオブジェクト，可以ための空。タグLIB_LOADがdataための{}のときは，それでも返却するhtml。
 * @return もしデータがなければdata，直接返す编译后的函数；存在する場合data，返すhtml。
 * @author wangxiao 
 * @email 1988wangxiao@gmail.com
*/

;(function(window){

    //ブラウザ環境の名前空間を取得しbaidu名前空間，非ブラウザ環境ではcommonjs仕様に準拠してexportsエクスポートする
    //～を修正しnodejs環境下で，を用いるbaidu.template変数名
    var baidu = typeof module === 'undefined' ? (window.baidu = window.baidu || {}) : module.exports;

    //テンプレート関数（配置されるbaidu.template名前空間内）
    baidu.template = function(str, data){

        //対象のid要素が存在するか確認し，要素がある場合はそのinnerHTML/value，なければ文字列をテンプレートとみなす
        var fn = (function(){

            //document がなければdocument，ブラウザ以外の環境と判断する
            if(!window.document){
                return bt._compile(str);
            };

            //HTML5規定ではID空白文字を含まない任意の文字列で構成できる
            var element = document.getElementById(str);
            if (element) {
                    
                //対応するidのdom，缓存其编译后のHTMLテンプレート関数
                if (bt.cache[str]) {
                    return bt.cache[str];
                };

                //textareaまたはinputの場合は value を取得しvalue，それ以外はinnerHTML
                var html = /^(textarea|input)$/i.test(element.nodeName) ? element.value : element.innerHTML;
                return bt._compile(html);

            }else{

                //テンプレート文字列であれば，関数を生成する
                //文字列を直接テンプレートとして渡した場合，変更が多くなる可能性があるため，キャッシュは行わない
                return bt._compile(str);
            };

        })();

        //データがあればそれを返すHTML文字列，没データがあればそれを返す函数 サポートdata={}の場合に対応
        var result = bt._isObject(data) ? fn( data ) : fn;
        fn = null;

        return result;
    };

    //名前空間を取得 baidu.template
    var bt = baidu.template;

    //現在のバージョンを示す
    bt.versions = bt.versions || [];
    bt.versions.push('1.0.6');

    //キャッシュ  対応するid模板生成的函数キャッシュ下来。
    bt.cache = {};
    
    //区切り記号をカスタマイズ，正規表現の文字を含めることができる，～でもよいHTMLコメントの開始部分 <! !>
    bt.LEFT_DELIMITER = bt.LEFT_DELIMITER||'<%';
    bt.RIGHT_DELIMITER = bt.RIGHT_DELIMITER||'%>';

    //デフォルトでエスケープするかを設定，デフォルトでは自動エスケープ
    bt.ESCAPE = true;

    //HTMLエスケープ
    bt._encodeHTML = function (source) {
        return String(source)
            .replace(/&/g,'&amp;')
            .replace(/</g,'&lt;')
            .replace(/>/g,'&gt;')
            .replace(/\\/g,'&#92;')
            .replace(/"/g,'&quot;')
            .replace(/'/g,'&#39;');
    };

    //正規表現に影響する文字をエスケープする
    bt._encodeReg = function (source) {
        return String(source).replace(/([.*+?^=!:${}()|[\]/\\])/g,'\\$1');
    };

    //エスケープUI UI変数をHTMLページタグのonclickなどのイベント関数の引数で使用する場合にエスケープ
    bt._encodeEventHTML = function (source) {
        return String(source)
            .replace(/&/g,'&amp;')
            .replace(/</g,'&lt;')
            .replace(/>/g,'&gt;')
            .replace(/"/g,'&quot;')
            .replace(/'/g,'&#39;')
            .replace(/\\\\/g,'\\')
            .replace(/\\\//g,'\/')
            .replace(/\\n/g,'\n')
            .replace(/\\r/g,'\r');
    };

    //文字列を連結して関数を生成する，すなわちコンパイル処理(compile)
    bt._compile = function(str){
        var funBody = "var _template_fun_array=[];\nvar fn=(function(__data__){\nvar _template_varName='';\nfor(name in __data__){\n_template_varName+=('var '+name+'=__data__[\"'+name+'\"];');\n};\neval(_template_varName);\n_template_fun_array.push('"+bt._analysisStr(str)+"');\n_template_varName=null;\n})(_template_object);\nfn = null;\nreturn _template_fun_array.join('');\n";
        return new Function("_template_object",funBody);
    };

    //が Object 型かどうかを判定Objectタイプ
    bt._isObject = function (source) {
        return 'function' === typeof source || !!(source && 'object' === typeof source);
    };

    //テンプレート文字列を解析
    bt._analysisStr = function(str){

        //区切り記号を取得
        var _left_ = bt.LEFT_DELIMITER;
        var _right_ = bt.RIGHT_DELIMITER;

        //区切り記号をエスケープし，正規表現のメタ文字をサポート，～でもよいHTMLコメント <!  !>
        var _left = bt._encodeReg(_left_);
        var _right = bt._encodeReg(_right_);

        str = String(str)
            
            //区切り記号内のjsコメント
            .replace(new RegExp("("+_left+"[^"+_right+"]*)//.*\n","g"), "$1")

            //コメント内容を削除  <%* ここには任意のコメントを記述できます *%>
            //デフォルトでHTMLコメント，をHTMLコメント匹配掉的原因是用户有可能用 <! !>を区切り記号として使用する可能性があるため
            .replace(new RegExp("<!--.*?-->", "g"),"")
            .replace(new RegExp(_left+"\\*.*?\\*"+_right, "g"),"")

            //すべての改行を削除  \r復帰文字 \tタブ文字 \n改行文字
            .replace(new RegExp("[\\r\\t\\n]","g"), "")

            //区切り文字以外の内部の内容に含まれる スラッシュ \ シングルクォート ‘ ，処理方法はHTMLエスケープ
            .replace(new RegExp(_left+"(?:(?!"+_right+")[\\s\\S])*"+_right+"|((?:(?!"+_left+")[\\s\\S])+)","g"),function (item, $1) {
                var str = '';
                if($1){

                    //を スラッシュ シングルクォート HTMLエスケープ
                    str = $1.replace(/\\/g,"&#92;").replace(/'/g,'&#39;');
                    while(/<[^<]*?&#39;[^<]*?>/g.test(str)){

                        //タグ内のシングルクォートを次のようにエスケープ\r  最後のステップと組み合わせて，に置き換える\'
                        str = str.replace(/(<[^<]*?)&#39;([^<]*?>)/g,'$1\r$2')
                    };
                }else{
                    str = item;
                }
                return str ;
            });


        str = str 
            //変数を定義，セミコロンがない場合，エラーに寛容に対応する必要がある  <%var val='test'%>
            .replace(new RegExp("("+_left+"[\\s]*?var[\\s]*?.*?[\\s]*?[^;])[\\s]*?"+_right,"g"),"$1;"+_right_)

            //変数の後ろのセミコロンを許容する(エスケープモードを含む 例<%:h=value%>)  <%=value;%> 関数の場合を除外 <%fun1();%> 変数定義の場合を除外  <%var val='test';%>
            .replace(new RegExp("("+_left+":?[hvu]?[\\s]*?=[\\s]*?[^;|"+_right+"]*?);[\\s]*?"+_right,"g"),"$1"+_right_)

            //に従って <% 配列に分割する，さらに \t 結合する，つまり、次のものを <% に置き換える \t
            //テンプレートを次の文字で<%一つ一つのセクションに分け，さらに各セクションの末尾に \t,つまり \t 各テンプレート断片の前で区切る
            .split(_left_).join("\t");

        //デフォルトで自動エスケープするかどうかの設定をサポート
        if(bt.ESCAPE){
            str = str

                //見つけて \t=任意の1文字%> に置き換える ‘，任意の文字,'
                //つまり単純な変数を置き換える  \t=data%> に置き換える ',data,'
                //デフォルトHTMLエスケープ  またサポートHTMLエスケープ写法<%:h=value%>  
                .replace(new RegExp("\\t=(.*?)"+_right,"g"),"',typeof($1) === 'undefined'?'':baidu.template._encodeHTML($1),'");
        }else{
            str = str
                
                //默认不エスケープHTMLエスケープ
                .replace(new RegExp("\\t=(.*?)"+_right,"g"),"',typeof($1) === 'undefined'?'':$1,'");
        };

        str = str

            //サポートHTMLエスケープ記法<%:h=value%>  
            .replace(new RegExp("\\t:h=(.*?)"+_right,"g"),"',typeof($1) === 'undefined'?'':baidu.template._encodeHTML($1),'")

            //エスケープしない記法をサポート <%:=value%>と<%-value%>
            .replace(new RegExp("\\t(?::=|-)(.*?)"+_right,"g"),"',typeof($1)==='undefined'?'':$1,'")

            //サポートurlエスケープ <%:u=value%>
            .replace(new RegExp("\\t:u=(.*?)"+_right,"g"),"',typeof($1)==='undefined'?'':encodeURIComponent($1),'")

            //サポートUI 変数をHTMLページタグのonclickなどのイベント関数の引数で使用する場合にエスケープ  <%:v=value%>
            .replace(new RegExp("\\t:v=(.*?)"+_right,"g"),"',typeof($1)==='undefined'?'':baidu.template._encodeEventHTML($1),'")

            //文字列を次の文字で \t 分成ための数组，さらに'); それらを結合し，つまり末尾の \t ための ');
            //でif，forなどの文の前に次の文字を追加し '); ，を形成する ');if  ');for  という形式にする
            .split("\t").join("');")

            //を %> に置き換える_template_fun_array.push('
            //つまり末尾の区切り記号を削除し，関数内のpushメソッド
            //例：if(list.length=5){%><h2>',list[4],'</h2>');}
            //に置き換えられる if(list.length=5){_template_fun_array.push('<h2>',list[4],'</h2>');}
            .split(_right_).join("_template_fun_array.push('")

            //を \r に置き換える \
            .split("\r").join("\\'");

        return str;
    };

})(window);
