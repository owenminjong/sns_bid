<!DOCTYPE html>
<html lang="ko-KR">

<head>
  <?php include './inc/head.php'?>
  <script src="js/index.js?v=<?=date("YmdHis")?>"></script>
</head>
<body id="index">

  <div id="login_box">
    <h1 id="logo"><img src="img/logo_white.png"></h1>
    <ul>
      <li>
        <span class="input">
          <input type="text" placeholder="아이디를 입력하세요." autocomplete="one-time-code" id="id"<?php echo get_cookie('ck_snsbid_id') ? 'value="'.get_cookie('ck_snsbid_id').'"' : '';?>/>
          <img src="img/user.svg" class="icon_login"/>
        </span>
      </li>
      <li>
        <span class="input">
          <input type="password" placeholder="비밀번호를 입력하세요." autocomplete="new-password" id="pw"<?php echo get_cookie('ck_snsbid_id') ? 'value="'.get_cookie('ck_snsbid_pw').'"' : '';?>/>
          <img src="img/pw.svg" class="icon_login"/>
        </span>
      </li>
      <li>
        <a href="javascript:;" class="btn btn-login">로그인</a>
      </li>
    </ul>
  </div>
  <div class="right">
    <div class="txt_box">
      <h2>차별화된<br>입찰 프로그램<br>숭늉샘BID</h2>
      <p>숭늉샘BID의 노하우!<br>낙찰의 기쁨을 함께 만들어 갑니다.</p>
    </div>
    <div class="img_box">
      <img src="img/index_bg.jpg">
    </div>
  </div>
</body>
</html>
