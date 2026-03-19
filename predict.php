<!DOCTYPE html>
<html lang="ko-KR">
<head>
  <?php include './inc/head.php'?>
  <script src="js/predict.js<?php echo "?v=".date("ymdhis");?>"></script>
  <style>
    /* popup */
    #popup_wrap {
      width: 100vw;
      height: 100vh;
      background-color: rgba(0, 0, 0, .6);
      position: fixed;
      left: 0;
      top: 0;
      display: none;
      z-index: 99990;
      user-select: none
    }
    #load {
      width: 230px;
      height: 130px;
      top: 0;
      left: 0;
      position: fixed;
      display: block;
      z-index: 999999;
      text-align: center;
      bottom: 0;
      right: 0;
      margin: auto;
    }

    #load>img:nth-child(1) {
      width: 50px
    }
  </style>
</head>
<body id="popupPredict">
  <div id="popup_wrap"></div>
  <div id="load" style="display:none;">
    <img src="./img/loading.gif" alt="loading">
  </div>
  <div id="popupPredictContainer">
    <h2>입찰예측</h2>
    <ul>
      <li>
        <label class="tit">기초금액</label>
        <div class="input cost">
          <input type="text" id="bcost" name="bcost" value="0"/>
          <em class="won">원</em>
        </div>
      </li>
      <li>
        <label class="tit">A값</label>
        <div class="input cost">
          <input type="text" id="acost" name="acost" value="0"/>
          <em class="won">원</em>
        </div>
      </li>
      <li>
        <label class="tit">순공사원가</label>
        <div class="input cost">
          <input type="text" id="nccost" name="nccost" value="0"/>
          <em class="won">원</em>
        </div>
      </li>
      <li>
        <label class="tit">하한율</label>
        <div class="input cost">
          <input type="text" id="mrcost" name="mrcost" value="0"/>
          <em class="won">원</em>
        </div>
      </li>
      <li class="btn_wrap full-width text-right">
        <a href="javascript:;" class="btn bg-whitegray btn_reset">초기화</a>
        <a href="javascript:;" class="btn bg-333 text-white btn_calculating_price">예측가 산출</a>
      </li>
    </ul>
    <ul class="prediction_successful_bid text-right">
      <li>
        <label class="tit">낙찰 예측가</label>
        <div class="input cost readonly">
          <input class="text-right" type="text" id="sbprice" name="sbprice" value="" readonly/>
          <em class="won">원</em>
        </div>
      </li>
    </ul>
  </div><!-- container -->
</body>
</html>
