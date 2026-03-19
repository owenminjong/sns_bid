<?php
header('Content-Type: text/html; charset=UTF-8');
header("Access-Control-Allow-Methods: GET, POST");
$return_array = array();

$bcost = $_REQUEST['bcost'];
$acost = $_REQUEST['acost'];
$mrcost = $_REQUEST['mrcost'];
$nccost = $_REQUEST['nccost'];

$str = "";

// 리눅스 서버 경로 → Windows 로컬 경로로 수정
//$str = "cd /home/snsbid/python/ && python3 sns_predict_web.py " . $bcost . " " . $acost . " '" . $mrcost . "' ".$nccost;
$str = "cd C:\\xampp\\htdocs\\snsbid\\python && python sns_predict_web.py " . $bcost . " " . $acost . " " . $mrcost . " " . $nccost;

exec($str,$output);

$row_array['body'] = $output[0];
//$row_array['str'] = $str;

array_push($return_array, $row_array);

echo json_encode($return_array,JSON_UNESCAPED_UNICODE);

?>