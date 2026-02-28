<?php

declare(strict_types=1);

namespace Yansongda\Pay\Plugin\Wechat;

use Closure;
use Yansongda\Pay\Contract\PluginInterface;
use Yansongda\Pay\Logger;
use Yansongda\Pay\Rocket;
use Yansongda\Supports\Str;

class PreparePlugin implements PluginInterface
{
    public function assembly(Rocket $rocket, Closure $next): Rocket
    {
        Logger::debug('[wechat][PreparePlugin] プラグインの読み込みを開始', ['rocket' => $rocket]);

        $rocket->mergePayload($this->getPayload($rocket->getParams()));

        Logger::info('[wechat][PreparePlugin] プラグインの読み込み完了', ['rocket' => $rocket]);

        return $next($rocket);
    }

    protected function getPayload(array $params): array
    {
        return array_filter($params, fn ($v, $k) => !Str::startsWith(strval($k), '_'), ARRAY_FILTER_USE_BOTH);
    }
}
