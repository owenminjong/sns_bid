<?php
header("Content-Type:application/json;charset=utf-8");
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

$inpay   = $_REQUEST["inpay"];
$bssamt  = $_REQUEST["bssamt"];
$Aamt    = $_REQUEST["Aamt"];
$realAmt = $_REQUEST["realAmt"];
$sucRate = $_REQUEST["sucRate"];
$plnprc  = $_REQUEST["plnprc"];

try {
    if ( empty($member['id']) ) throw new Exception("로그인 상태가 아닙니다. 로그인해주세요.");
    if ( $bssamt == "0" || strlen($bssamt) == 0 ) throw new Exception("기초금액을 입력하여 주시기 바랍니다.");
    if ( $Aamt == "0" || strlen($Aamt) == 0 ) throw new Exception("A값을 입력하여 주시기 바랍니다.");
    if ( $sucRate == "0" || strlen($sucRate) == 0 ) throw new Exception("하한율을 입력하여 주시기 바랍니다.");
    if ( $inpay == "0" || strlen($inpay) == 0 ) throw new Exception("예측가를 산출하여 주시기 바랍니다.");

    $sql = "CALL Get_InputRate_sp(:inpay, :bssamt, :Aamt, :realAmt, :sucRate, :plnprc)";

    $stmt = $pdo->prepare($sql);
    $stmt->bindValue(":inpay",   $inpay);
    $stmt->bindValue(":bssamt",  $bssamt);
    $stmt->bindValue(":Aamt",    $Aamt);
    $stmt->bindValue(":realAmt", $realAmt);
    $stmt->bindValue(":sucRate", $sucRate);
    $stmt->bindValue(":plnprc",  $plnprc);

    $stmt->execute();
    $row = $stmt->fetch(PDO::FETCH_ASSOC);

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