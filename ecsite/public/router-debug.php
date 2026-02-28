<?php
// +----------------------------------------------------------------------
// | ThinkPHP [ WE CAN DO IT JUST THINK ]
// +----------------------------------------------------------------------
// | Copyright (c) 2006~2016 http://thinkphp.cn All rights reserved.
// +----------------------------------------------------------------------
// | Licensed ( http://www.apache.org/licenses/LICENSE-2.0 )
// +----------------------------------------------------------------------
// | Author: liu21st <liu21st@gmail.com>
// +----------------------------------------------------------------------
// $Id$

// 调试日志
error_log("=== Router Debug ===");
error_log("REQUEST_URI: " . $_SERVER["REQUEST_URI"]);
error_log("SCRIPT_NAME: " . $_SERVER["SCRIPT_NAME"]);
error_log("DOCUMENT_ROOT: " . $_SERVER["DOCUMENT_ROOT"]);

$requested_file = $_SERVER["DOCUMENT_ROOT"] . $_SERVER["SCRIPT_NAME"];
error_log("Checking file: " . $requested_file);
error_log("File exists: " . (is_file($requested_file) ? "YES" : "NO"));

if (is_file($requested_file)) {
    error_log("Action: Return false (file exists)");
    return false;
} else {
    error_log("Action: Route to index.php");
    $_SERVER["SCRIPT_FILENAME"] = __DIR__ . '/index.php';
    require __DIR__ . "/index.php";
}
