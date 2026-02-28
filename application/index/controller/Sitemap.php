<?php

namespace app\index\controller;

use app\common\model\Goods;
use app\common\model\News;
use think\Db;

class Sitemap extends Base
{
    protected $noNeedLogin = '*';
    protected $noNeedRight = '*';

    /**
     * サイトマップXMLを生成
     */
    public function index()
    {
        // XMLヘッダーを設定
        header('Content-Type: application/xml; charset=utf-8');

        $domain = $this->request->domain();
        $xml = '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
        $xml .= '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";

        // 1. ホームページ
        $xml .= $this->addUrl($domain . '/', date('Y-m-d'), 'daily', '1.0');

        // 2. 静的ページ
        $staticPages = [
            '/goods' => ['changefreq' => 'daily', 'priority' => '0.9'],
            '/news' => ['changefreq' => 'daily', 'priority' => '0.8'],
            '/shop' => ['changefreq' => 'monthly', 'priority' => '0.7'],
            '/buy_way' => ['changefreq' => 'monthly', 'priority' => '0.7'],
            '/guide' => ['changefreq' => 'monthly', 'priority' => '0.7'],
            '/faq' => ['changefreq' => 'monthly', 'priority' => '0.6'],
            '/contactus' => ['changefreq' => 'monthly', 'priority' => '0.5'],
            '/trading_law' => ['changefreq' => 'yearly', 'priority' => '0.4'],
            '/use_terms' => ['changefreq' => 'yearly', 'priority' => '0.4'],
            '/privacy_policy' => ['changefreq' => 'yearly', 'priority' => '0.4'],
        ];

        foreach ($staticPages as $url => $config) {
            $xml .= $this->addUrl(
                $domain . $url,
                date('Y-m-d'),
                $config['changefreq'],
                $config['priority']
            );
        }

        // 3. 商品カテゴリページ
        $categories = Db::name('category')
            ->where('type', 'goods')
            ->where('status', 'normal')
            ->order('weigh desc')
            ->select();

        foreach ($categories as $category) {
            if ($category['pid'] == 0) {
                // 第一階層カテゴリ
                $xml .= $this->addUrl(
                    $domain . '/goods/' . $category['id'],
                    date('Y-m-d'),
                    'daily',
                    '0.8'
                );
            }
        }

        // 4. 商品詳細ページ
        $goods = Goods::where('status', 'normal')
            ->order('weigh desc, id desc')
            ->limit(1000) // 最大1000件
            ->select();

        foreach ($goods as $item) {
            $lastmod = $item['updatetime'] ? date('Y-m-d', $item['updatetime']) : date('Y-m-d', $item['createtime']);
            $xml .= $this->addUrl(
                $domain . '/gdetails/' . $item['id'],
                $lastmod,
                'weekly',
                '0.6'
            );
        }

        // 5. ニュース詳細ページ
        $news = News::where('status', 'normal')
            ->order('weigh desc, id desc')
            ->limit(500) // 最大500件
            ->select();

        foreach ($news as $item) {
            $lastmod = $item['updatetime'] ? date('Y-m-d', $item['updatetime']) : date('Y-m-d', $item['createtime']);
            $xml .= $this->addUrl(
                $domain . '/ndetails/' . $item['id'],
                $lastmod,
                'monthly',
                '0.5'
            );
        }

        $xml .= '</urlset>';

        return $xml;
    }

    /**
     * URL要素を追加
     */
    private function addUrl($loc, $lastmod, $changefreq, $priority)
    {
        $xml = "  <url>\n";
        $xml .= "    <loc>" . htmlspecialchars($loc) . "</loc>\n";
        $xml .= "    <lastmod>" . $lastmod . "</lastmod>\n";
        $xml .= "    <changefreq>" . $changefreq . "</changefreq>\n";
        $xml .= "    <priority>" . $priority . "</priority>\n";
        $xml .= "  </url>\n";
        return $xml;
    }
}
