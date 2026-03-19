
  <header id="header">
      <div class="header_info text-left">
        <a href="tender_notice.php" id="header_logo" class="float-left"><img src='img/logo.png'></a>

        <nav id="gnb">
          <ul >
            <li onclick="location.href='tender_notice.php'">입찰공고</h3></li>
            <li onclick="location.href='prediction_list.php'">예측내역</h3></li>
            <?php if ($_SESSION['snsbid_issvr'] == 1) {?>
            <li onclick="location.href='batch_log.php'">Batch Log</h3></li>
            <li onclick="location.href='user_manage.php'">사용자 관리</li>
            <?php }?>
          </ul>
        </nav>


        <div class="float-right">
          <p class="top_btns text-right">
            <a href="javascript:;" class="btn btn_select_site"></a>
            <a href="javascript:;" class="login_name"><?php echo $headername;?>님</a>
            <a href="./ajax/logout.php" onClick="" class="btn bg-primary text-white">로그아웃</a>
          </p>

        </div>
      </div>
  </header>

  <div class="dimed"></div>

  <div id="load" style="display:none;">
    <img src="./img/loading.gif" alt="loading">
  </div>

  <!-- <a href="javascript:;" class="btn" data-bs-toggle="modal" data-bs-target="#popupConfirm">confirm</a> -->

  <div class="modal fade" id="popupConfirm" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="popupConfirmLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="popupConfirmLabel">입찰 예측</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">팝업내용</div>
        <div class="modal-footer">
          <a href="javascript:;" class="btn btn_ok">확인</a>
          <a href="javascript:;" data-bs-dismiss="modal" class="btn btn_cancel">취소</a>
        </div>
      </div>
    </div>
  </div>
