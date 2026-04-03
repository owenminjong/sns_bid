<?php
header("Content-Type:application/json;charset=utf-8");
header("Cache-Control: no-cache");
header("Pragma: no-cache");

include "./_config.php";
include "./var_db.php";  // ← 추가

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

    $sql = "CALL Staff_Login(:sfid, :sfpw)";

    $stmt = $pdo->prepare($sql);
    $stmt->bindValue(":sfid", $sfid);
    $stmt->bindValue(":sfpw", $sfpw);
    $stmt->execute();

    $row = $stmt->fetch(PDO::FETCH_ASSOC);

    $ret = $row['sfcode'];

    if ($ret <= 0) throw new Exception("없는 자료이거나 잘못된 자료입니다.|없는 자료이거나 잘못된 자료입니다.");

    setcookie(md5('ck_snsbid_id'), base64_encode($sfid), time() + 86400 * 60, "/");
    setcookie(md5('ck_snsbid_pw'), base64_encode($sfpw), time() + 86400 * 60, "/");

    $_SESSION['snsbid_id']    = $sfid;
    $_SESSION['snsbid_code']  = $ret;
    $_SESSION['snsbid_name']  = $row['sfname'];
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