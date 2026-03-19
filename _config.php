<?php
  date_default_timezone_set('Asia/Seoul');
  session_set_cookie_params( 86400 * 30, '/' ); // 세션 만료시간 한달동안 연장
  session_regenerate_id( false ); // 현재 세션 id 새로 갱신하지 않음
  session_cache_expire(43200); // 세션유지시간을 43200시간으로 설정 (30일), 설정은 분 단위
  ini_set("session.cache_expire", 2592000);   // 세션 만료시간을 한달로 설정
  ini_set("session.gc_maxlifetime", 2592000);  // 움직임이 없을 경우 한달로 설정
  session_start();
  if (isset($global_ajax) === false) {
    include "./accessCheck.php";
  }
?>