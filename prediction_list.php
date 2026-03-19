<!DOCTYPE html>
<html lang="ko-KR">

<head>
  <?php include './inc/head.php'?>
  <script src="js/prediction_list.js?v=<?=date("YmdHis")?>"></script>
  <style>
		.onetable {table-layout: fixed;}
    .oneline {overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
  </style>
</head>
<body id="prediction_list">
  <?php include './inc/header.php'?>
  <div id="container">
    <div class="cont_inner">
        <div class="searchbox">
          <ul>
            <li>
              <label class="tit">개찰기간</label>
              <div class="date_input">
                <span class=" input">
                  <input type="text" id="fdate" name="fdate" value="" class="txt_date" onkeypress="hyphenAdd(this,4);" onblur="dateInputCheck(this);" maxlength="10"/>
                </span>
                <span class="wave">~</span>
                <span class=" input">
                  <input type="text" id="tdate" name="tdate" value="" class="txt_date" onkeypress="hyphenAdd(this,4);" onblur="dateInputCheck(this);" maxlength="10"/>
                </span>
              </div>
            </li>
            <li>
              <label class="tit">공고번호</label>
              <div class="input">
                <input type="text" id="bidNtceNo" name="bidNtceNo" value=""/>
              </div>
            </li>
            <li class="construction_name">
              <label class="tit">공사명</label>
              <div class="input">
                <input type="text" id="bidNtceNm" name="bidNtceNm" value=""/>
              </div>
            </li>
            <li class="construction_name">
              <label class="tit">낙찰업체</label>
              <div class="input">
                <input type="text" id="comp" name="comp" value=""/>
              </div>
            </li>
            <li class="btn_wrap">
              <a href="javascript:;" class="btn" id="btn_search">조회</a>
            </li>
          </ul>
        </div>
        <div class="table_area">
          <table class="onetable">
            <colgroup>
              <col width="130px"/>
              <col width="90px"/>
              <col width="130px"/>
              <col width="330px"/>
              <col width="140px"/>
              <col width="140px"/>
              <col width="140px"/>
              <col width="140px"/>
              <!--<col width="80px"/>
              <col width="80px"/>-->
              <col width="120px"/>
              <!--<col width="140px"/>-->
              <col width="180px"/>
              <col width="140px"/>
              <!--<col width="80px"/>
              <col width="80px"/>-->
              <col width="120px"/>
              <col width="80px"/>
              <col width="140px"/>
            </colgroup>
            <thead>
              <th>개찰일자</th>
              <th>예측일자</th>
              <th>공고번호</th>
              <th>공사명<!-- <a href="javascript:;" class="btn btn_remarks" data-bs-toggle="modal" data-bs-target="#popupRemarks">비고수정</a>--></th>
              <th>기초금액</th>
              <th>A값</th>
              <th>순공사원가</th>
              <th>예측금액</th>
              <!--<th>예측율</th>-->
              <th>예측사정률</th>
              <th>낙찰업체</th>
              <th>낙찰금액</th>
              <!--<th>낙찰율</th>-->
              <th>낙찰사정률</th>
              <th>담당자</th>
              <th>비고</th>
            </thead>
            <tbody id="list">
              <!--<tr>
                <td>2024-11-01</td>
                <td>2024-11-01</td>
                <td>2024000121-01</td>
                <td class="text-left">도시철도공사-건물공사</td>
                <td class="text-right">120,000,333</td>
                <td>87.745</td>
                <td class="text-right">67,900,112</td>
                <td class="text-right">89,000,333</td>
                <td class="text-right">67,900,112</td>
                <td>홍길동</td>
              </tr>-->
            </tbody>
          </table>
        </div>

        <nav class="pagnav">
          <ul class="pagination" id="listPage">
            <!--<li class="page-item page_custom active">
              <a class="page-link" href="javascript:;"><span>1</span></a>
            </li>
            <li class="page-item page_custom">
              <a class="page-link" href="javascript:;"><span>2</span></a>
            </li>
            <li class="page-item page_custom">
              <a class="page-link" href="javascript:;"><span>3</span></a>
            </li>-->
          </ul>
        </nav>
    </div><!-- cont_inner -->


    <div class="modal fade" id="popupRemarks" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="popupRemarksLabel" aria-hidden="true">
      <div class="popup modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="popupRemarksLabel">비고 수정</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <ul>
              <li>
                <label class="tit">공사명</label>
                <div class="input readonly">
                  <input type="text" id="popupName" name="popupName" value="" readonly/>
                  <input type="hidden" id="popupkey" name="popupkey" value="" readonly/>
                </div>
              </li>
              <li>
                <label class="tit">비고</label>
                <div class="input">
                  <input type="text" id="betc" name="betc" value=""/>
                </div>
              </li>
            </ul>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn bg-primary btn_save text-white">저장</button>
          </div>
        </div>
      </div>
    </div>


  </div><!-- container -->
  <?php include './inc/footer.php'?>
</body>
</html>
