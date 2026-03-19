<!DOCTYPE html>
<html lang="ko-KR">

<head>
  <?php include './inc/head.php'?>
  <script src="js/batch_log.js?v=<?=date("YmdHis")?>"></script>
</head>
<body id="batch_log">
  <?php include './inc/header.php'?>
  <div id="container">
    <div class="cont_inner">
        <div class="searchbox">
          <ul>
            <li>
              <label class="tit">작업기간</label>
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
              <label class="tit">작업구분</label>
              <div class="select">
                <select id="bkind" name="bkind">
                  <option value="-1">::전체::</option>
                  <option value="1">공고 API</option>
                  <option value="2">개찰 API</option>
                  <option value="3">예측모델생성</option>
                </select>
              </div>
            </li>
            <li class="btn_wrap">
              <a href="javascript:;" class="btn" id="btn_search">조회</a>
            </li>
          </ul>
        </div>
        <div class="table_area">
          <table>
            <colgroup>
              <col width="150px"/>
              <col width="150px"/>
              <col width="150px"/>
              <col width="150px"/>
              <col width="*" style="min-width:300px"/>
            <colgroup>
            <thead>
              <th>작업시작</th>
              <th>작업종료</th>
              <th>작업구분</th>
              <th>기준일자</th>
              <th>작업내용</th>
            </thead>
            <tbody id="list">
              <!--<tr>
                <td>2024-11-01 12:44</td>
                <td>2024-11-01 12:44</td>
                <td>입찰 공고 API</td>
                <td class="text-left">2024-11-01 ~ 2024-11-10 의 공사입찰공고 30건 저장</td>
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

  </div><!-- container -->
  <?php include './inc/footer.php'?>
</body>
</html>
