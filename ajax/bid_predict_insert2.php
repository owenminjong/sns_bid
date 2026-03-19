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

$bsn = $_REQUEST["bsn"];
$bidNtceNo = $_REQUEST["bidNtceNo"];
$bidNtceNm = $_REQUEST["bidNtceNm"];
$bssamt = $_REQUEST["bssamt"];
$Aamt = $_REQUEST["Aamt"];
$realAmt = $_REQUEST["realAmt"];
$urate = $_REQUEST["urate"];
$preamt = $_REQUEST["preamt"];
$betc = $_REQUEST["betc"];
$sfcode = $member['code'];

try {
  if ( empty($member['id']) )throw new Exception("로그인 상태가 아닙니다. 로그인해주세요.");
  if ( $bssamt == "0" || strlen($bssamt) == "0" )throw new Exception("기초금액을 입력하여 주시기 바랍니다.");
  if ( $Aamt == "0" || strlen($Aamt) == "0" )throw new Exception("A값을 입력하여 주시기 바랍니다.");
  if ( $urate == "0" || strlen($urate) == "0" )throw new Exception("하한율을 입력하여 주시기 바랍니다.");
  if ( $preamt == "0" || strlen($preamt) == "0" )throw new Exception("예측가를 산출하여 주시기 바랍니다.");

  $sql = "CALL bid_predict_insert2(:bsn, :bidNtceNo, :bidNtceNm, :bssamt, :Aamt, :realAmt, :urate, :betc, :preamt, :sfcode)";
  $sql_log = "CALL bid_predict_insert2($bsn, '$bidNtceNo', '$bidNtceNm', $bssamt, $Aamt, $realAmt, '$urate', '$betc', $preamt, $sfcode)";
  //error_log($sql_log."\n", 3, "../log/log-".date("Ymd").".log");

  $stmt = $pdo->prepare($sql);

  $stmt->bindValue(":bsn", $bsn);
  $stmt->bindValue(":bidNtceNo", $bidNtceNo);
  $stmt->bindValue(":bidNtceNm", $bidNtceNm);
  $stmt->bindValue(":bssamt", $bssamt);
  $stmt->bindValue(":Aamt", $Aamt);
  $stmt->bindValue(":realAmt", $realAmt);
  $stmt->bindValue(":urate", $urate);
  $stmt->bindValue(":betc", $betc);
  $stmt->bindValue(":preamt", $preamt);
  $stmt->bindValue(":sfcode", $sfcode);

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
    echo json_encode(array("msg" => $buf[0], "err" => $buf[1], "ret" => "-1"), JSON_UNESCAPED_UNICODE);
  else
    echo json_encode(array("msg" => $buf[0], "err" => "", "ret" => "-1"), JSON_UNESCAPED_UNICODE);
}
?>