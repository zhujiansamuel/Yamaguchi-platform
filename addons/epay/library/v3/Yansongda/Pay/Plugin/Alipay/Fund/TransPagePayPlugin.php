<?php

declare(strict_types=1);

namespace Yansongda\Pay\Plugin\Alipay\Fund;

use Closure;
use Yansongda\Pay\Contract\PluginInterface;
use Yansongda\Pay\Direction\ResponseDirection;
use Yansongda\Pay\Logger;
use Yansongda\Pay\Rocket;

/**
 * @see https://opendocs.alipay.com/open/03rbye
 */
class TransPagePayPlugin implements PluginInterface
{
    public function assembly(Rocket $rocket, Closure $next): Rocket
    {
        Logger::debug('[alipay][TransPagePayPlugin] プラグインの読み込みを開始', ['rocket' => $rocket]);

        $rocket->setDirection(ResponseDirection::class)
            ->mergePayload([
                'method' => 'alipay.fund.trans.page.pay',
                'biz_content' => $rocket->getParams(),
            ])
        ;

        Logger::info('[alipay][TransPagePayPlugin] プラグインの読み込み完了', ['rocket' => $rocket]);

        return $next($rocket);
    }
}
