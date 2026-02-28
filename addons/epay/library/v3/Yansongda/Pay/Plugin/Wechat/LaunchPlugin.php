<?php

declare(strict_types=1);

namespace Yansongda\Pay\Plugin\Wechat;

use Closure;
use Psr\Http\Message\MessageInterface;
use Psr\Http\Message\ResponseInterface;
use Yansongda\Pay\Contract\PluginInterface;
use Yansongda\Pay\Exception\ContainerException;
use Yansongda\Pay\Exception\Exception;
use Yansongda\Pay\Exception\InvalidConfigException;
use Yansongda\Pay\Exception\InvalidParamsException;
use Yansongda\Pay\Exception\InvalidResponseException;
use Yansongda\Pay\Exception\ServiceNotFoundException;
use Yansongda\Pay\Logger;
use Yansongda\Pay\Rocket;
use Yansongda\Supports\Collection;

use function Yansongda\Pay\should_do_http_request;
use function Yansongda\Pay\verify_wechat_sign;

class LaunchPlugin implements PluginInterface
{
    /**
     * @throws ContainerException
     * @throws InvalidConfigException
     * @throws InvalidResponseException
     * @throws ServiceNotFoundException
     * @throws InvalidParamsException
     */
    public function assembly(Rocket $rocket, Closure $next): Rocket
    {
        /* @var Rocket $rocket */
        $rocket = $next($rocket);

        Logger::debug('[wechat][LaunchPlugin] プラグインの読み込みを開始', ['rocket' => $rocket]);

        if (should_do_http_request($rocket->getDirection())) {
            verify_wechat_sign($rocket->getDestinationOrigin(), $rocket->getParams());

            $rocket->setDestination($this->validateResponse($rocket));
        }

        Logger::info('[wechat][LaunchPlugin] プラグインの読み込み完了', ['rocket' => $rocket]);

        return $rocket;
    }

    /**
     * @return null|array|Collection|MessageInterface
     *
     * @throws InvalidResponseException
     */
    protected function validateResponse(Rocket $rocket)
    {
        $response = $rocket->getDestination();

        if ($response instanceof ResponseInterface
            && ($response->getStatusCode() < 200 || $response->getStatusCode() >= 300)) {
            throw new InvalidResponseException(Exception::INVALID_RESPONSE_CODE);
        }

        return $response;
    }
}
