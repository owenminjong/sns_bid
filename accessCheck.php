<?php
  // 쿠키변수값 얻음
  function get_cookie($cookie_name) {
    return base64_decode($_COOKIE[md5($cookie_name)]);
  }
  if (basename($_SERVER['PHP_SELF']) !== 'index.php' && (isset($_SESSION['snsbid_id']) === false || $_SESSION['snsbid_id'] != get_cookie('ck_snsbid_id'))) {
    echo '<script>alert("로그인 상태가 아닙니다. 로그인해주세요.");location.href="./";</script>';
  }
  $headername = $_SESSION['snsbid_name'];
?>