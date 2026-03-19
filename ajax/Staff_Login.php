<?php
header("Content-Type:application/json;charset=utf-8");
// header('Access-Control-Allow-Origin: *');
// header("Access-Control-Allow-Headers: X-API-KEY, Origin, X-Requested-With, Content-Type, Accept, Access-Control-Request-Method");
// header("Access-Control-Allow-Methods: GET, POST, OPTIONS, PUT, DELETE");
header("Cache-Control: no-cache");
header("Pragma: no-cache");

include "./_config.php";

try {
  $pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8", $dbuser, $dbpass);
  $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $ex) {
  http_response_code(500);
  echo json_encode(array("msg" => $ex->getMessage()), JSON_UNESCAPED_UNICODE);
  return false;
}

$sfid = $_REQUEST["sfid"];
$sfpw = $_REQUEST["sfpw"];

try {
  if ( empty($sfid) )throw new Exception("아이디를 입력하지 않았습니다.");
  if ( empty($sfpw) )throw new Exception("비밀번호를 입력하지 않았습니다.");

  $sql = "CALL Staff_Login(:sfid, :sfpw)";
  $sql_log = "CALL Staff_Login('$sfid', '$sfpw')";
  //error_log($sql_log."\n", 3, "../log/log-".date("Ymd").".log");

  $stmt = $pdo->prepare($sql);

  $stmt->bindValue(":sfid", $sfid);
  $stmt->bindValue(":sfpw", $sfpw);

  $result = $stmt->execute();

  $row = $stmt->fetch(PDO::FETCH_ASSOC);

  $ret = $row['sfcode'];
  $err = "없는 자료이거나 잘못된 자료입니다.";
  $msg = "없는 자료이거나 잘못된 자료입니다.";

  if ($ret <= 0) throw new Exception("$err|$msg");
/*
  session_set_cookie_params( 86400 * 30, '/' ); // 세션 만료시간 한달동안 연장
  session_regenerate_id( false ); // 현재 세션 id 새로 갱신하지 않음
  session_cache_expire(43200); // 세션유지시간을 43200시간으로 설정 (30일), 설정은 분 단위
  ini_set("session.cache_expire", 2592000);   // 세션 만료시간을 한달로 설정
  ini_set("session.gc_maxlifetime", 2592000);  // 움직임이 없을 경우 한달로 설정

  setcookie(md5('ck_snsbid_id'),base64_encode($sfid),time() + 86400 * 60,"/");

  session_start();
*/

  setcookie(md5('ck_snsbid_id'),base64_encode($sfid),time() + 86400 * 60,"/");
  setcookie(md5('ck_snsbid_pw'),base64_encode($sfpw),time() + 86400 * 60,"/");

  $_SESSION['snsbid_id'] = $sfid;
  $_SESSION['snsbid_code'] = $ret;
  $_SESSION['snsbid_name'] = $row['sfname'];
  $_SESSION['snsbid_issvr'] = $row['issvr'];

  $link = array();
  $link['ret'] = 1;
  $link['link'] = "./tender_notice.php";

  http_response_code(200);
  echo json_encode($link, JSON_UNESCAPED_UNICODE);
} catch (Exception $ex) {
  http_response_code(500);
  $buf = explode("|", $ex->getMessage());

  if (count($buf) >= 2)
    echo json_encode(array("msg" => $buf[0], "err" => $buf[1]), JSON_UNESCAPED_UNICODE);
  else
    echo json_encode(array("msg" => $buf[0], "err" => ""), JSON_UNESCAPED_UNICODE);
}
?>