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

$sfname = $_REQUEST["sfname"];
$tel = $_REQUEST["tel"];
$sfid = $_REQUEST["sfid"];
$sfpw = $_REQUEST["sfpw"];
$resfpw = $_REQUEST["resfpw"];
$issvr = $_REQUEST["issvr"];
$isuse = $_REQUEST["isuse"];

try {
  if ( empty($member['id']) )throw new Exception("로그인 상태가 아닙니다. 로그인해주세요.");
  if ( empty($sfname) )throw new Exception("이름을 입력하지 않았습니다.");
  if ( empty($tel) )throw new Exception("전화번호를 입력하지 않았습니다.");
  if ( empty($sfid) )throw new Exception("아이디를 입력하지 않았습니다.");
  if ( empty($sfpw) )throw new Exception("비밀번호를 입력하지 않았습니다.");
  if ( empty($resfpw) )throw new Exception("비밀번호확인을 입력하지 않았습니다.");
  if ( $sfpw != $resfpw )throw new Exception("입력한 비밀번호가 다릅니다.");

  if (!$issvr) {
    $issvr = 0;
  } elseif ($issvr) {
    $issvr = $issvr;
  }

  if (!$isuse) {
    $isuse = 0;
  } elseif ($isuse) {
    $isuse = $isuse;
  }

  if ( strlen($sfid) > 20 )throw new Exception("아이디를 20자리 이하로 입력해 주세요.");

  $sql = "CALL Staff_Insert(:sfname, :tel, :sfid, :sfpw, :issvr, :isuse)";
  $sql_log = "CALL Staff_Insert('$sfname', '$tel', '$sfid', '$sfpw', $issvr, $isuse)";
  //error_log($sql_log."\n", 3, "../log/log-".date("Ymd").".log");

  $stmt = $pdo->prepare($sql);

  $stmt->bindValue(":sfname", $sfname);
  $stmt->bindValue(":tel", $tel);
  $stmt->bindValue(":sfid", $sfid);
  $stmt->bindValue(":sfpw", $sfpw);
  $stmt->bindValue(":issvr", $issvr);
  $stmt->bindValue(":isuse", $isuse);

  $result = $stmt->execute();

  $row = $stmt->fetch(PDO::FETCH_ASSOC);

  $ret = $row["ret"];
  $err = $row["err"];
  $state = $row["state"]; // SQL state
  $msg = $row["msg"];     // SQL system message

  if ($ret <= 0) throw new Exception("$err|$msg");

  http_response_code(200);
  echo json_encode($row, JSON_UNESCAPED_UNICODE);
} catch (Exception $ex) {
  http_response_code(500);
  $buf = explode("|", $ex->getMessage());

  if (count($buf) >= 2)
    echo json_encode(array("msg" => $buf[0], "err" => $buf[1]), JSON_UNESCAPED_UNICODE);
  else
    echo json_encode(array("msg" => $buf[0], "err" => ""), JSON_UNESCAPED_UNICODE);
}
?>