var express = require('express');
var template = require('../node/template.js');


var app = module.exports = express();

template.config('extname', '.html');
app.engine('.html', template.__express);
app.set('view engine', 'html');
app.set('views', __dirname + '/node-template');


var demoData = {
  title: '国内ニュース',
  time: (new Date).toString(),
  list: [
    {
      title: '<原油価格>調整サイクルを短縮して10営業日 拡張なし4%変動幅の制限',
      url: 'http://finance.qq.com/zt2013/2013yj/index.htm'
    },
    {
      title: '明日からガソリン価格をトン当たり引き下げ310元 単価が回帰して7元の時代に',
      url: 'http://finance.qq.com/a/20130326/007060.htm'
    },
    {
      title: '広東省の副県長が愛人を捨てた疑いで6女性たちに集団暴行される 規律検査による調査',
      url: 'http://news.qq.com/a/20130326/001254.htm'
    },
    {
      title: '湖南省27歳の副県長が疑問に回答：父はもはや指導者ではない',
      url: 'http://news.qq.com/a/20130326/000959.htm'
    },
    {
      title: '北朝鮮軍が戦闘勤務態勢に入る いつでも米国へのミサイル攻撃の準備ができていると表明',
      url: 'http://news.qq.com/a/20130326/001307.htm'
    }
  ]
};

app.get('/', function(req, res){
  res.render('./index', demoData);
});

/* istanbul ignore next */
if (!module.parent) {
  app.listen(3000);
  console.log('Express started on port 3000');
}