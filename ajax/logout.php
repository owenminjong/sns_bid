<?php
  session_start();
  unset($_SESSION['snsbid_id']);
  unset($_SESSION['snsbid_code']);
  unset($_SESSION['snsbid_name']);
  unset($_SESSION['snsbid_issvr']);

	//setcookie(md5('ck_snsbid_id'), '', time()-42000, '/');

  header('location:../');
?>