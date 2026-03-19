<?php
date_default_timezone_set('Asia/Seoul');

// 세션 설정은 session_start() 전에 해야 함
session_set_cookie_params( 86400 * 30, '/' );
session_cache_expire(43200);
ini_set("session.cache_expire", 2592000);
ini_set("session.gc_maxlifetime", 2592000);

if (session_status() === PHP_SESSION_NONE) {
    session_start();
    session_regenerate_id( false );
}

if (isset($global_ajax) === false) {
    include "./accessCheck.php";
}
?>