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

$fdate = $_REQUEST["fdate"];
$tdate = $_REQUEST["tdate"];
$bidNtceNo = $_REQUEST["bidNtceNo"];
$bidNtceNm = $_REQUEST["bidNtceNm"];
$comp = $_REQUEST["comp"];
$psize = $_REQUEST["psize"];
$sfcode = $member['code'];
$cpage = $_REQUEST["cpage"];

try {
  $sql = "CALL bid_predict_List2(:fdate, :tdate, :bidNtceNo, :bidNtceNm, :comp, :sfcode, :psize, :cpage)";
  $sql_log = "CALL bid_predict_List2('$fdate', '$tdate', '$bidNtceNo', '$bidNtceNm', '$comp', $sfcode, $psize, $cpage)";
  error_log($sql_log."\n", 3, "../log/log-".date("Ymd").".log");

  $stmt = $pdo->prepare($sql);

  $stmt->bindValue(":fdate", $fdate);
  $stmt->bindValue(":tdate", $tdate);
  $stmt->bindValue(":bidNtceNo", $bidNtceNo);
  $stmt->bindValue(":bidNtceNm", $bidNtceNm);
  $stmt->bindValue(":comp", $comp);
  $stmt->bindValue(":sfcode", $sfcode);
  $stmt->bindValue(":psize", $psize);
  $stmt->bindValue(":cpage", $cpage);

  $result = $stmt->execute();

  $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

  // 페이지 처리
  $sql = "CALL bid_predict_ListCount2(:fdate, :tdate, :bidNtceNo, :bidNtceNm, :comp, :sfcode, :psize)";
  $sql_log = "CALL bid_predict_ListCount2('$fdate', '$tdate', '$bidNtceNo', '$bidNtceNm', '$comp', $sfcode, $psize)";
  error_log($sql_log."\n", 3, "../log/log-".date("Ymd").".log");

  $stmt = $pdo->prepare($sql);

  $stmt->bindValue(":fdate", $fdate);
  $stmt->bindValue(":tdate", $tdate);
  $stmt->bindValue(":bidNtceNo", $bidNtceNo);
  $stmt->bindValue(":bidNtceNm", $bidNtceNm);
  $stmt->bindValue(":comp", $comp);
  $stmt->bindValue(":sfcode", $sfcode);
  $stmt->bindValue(":psize", $psize);

  $result = $stmt->execute();

  $row = $stmt->fetch(PDO::FETCH_ASSOC);

  $tpage = $row["tpage"];
  $trec = $row["trec"];

  http_response_code(200);
  echo json_encode(array("list" => $rows, "tpage" => $tpage, "trec" => $trec), JSON_UNESCAPED_UNICODE);
} catch (Exception $ex) {
  http_response_code(500);
  $buf = explode("|", $ex->getMessage());

  if (count($buf) >= 2)
    echo json_encode(array("msg" => $buf[0], "err" => $buf[1]), JSON_UNESCAPED_UNICODE);
  else
    echo json_encode(array("msg" => $buf[0], "err" => ""), JSON_UNESCAPED_UNICODE);
}
?>