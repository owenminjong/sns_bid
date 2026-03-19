<!DOCTYPE html>
<html lang="ko-KR">

<head>
  <?php include './inc/head.php'?>
  <script src="js/tender_notice.js?v=<?=date("YmdHis")?>"></script>
  <style>
    #load {
      z-index: 999999;
    }
		.onetable {table-layout: fixed;}
    .oneline {overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
  </style>
</head>
<body id="tender_notice">
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
            <li>
              <label class="tit">개찰여부</label>
              <div class="select">
                <select id="isopen" name="isopen">
                  <option value="-1">::전체::</option>
                  <option value="1">개찰</option>
                  <option value="0">미개찰</option>
                </select>
              </div>
            </li>
            <li>
              <label class="tit">기초금액</label>
              <div class="cost_input">
                <span class=" input">
                  <input type="text" id="famt" name="famt" value="" class="text-right"/>
                  <em class="won">원</em>
                </span>
                <span class="wave">~</span>
                <span class=" input">
                  <input type="text" id="tamt" name="tamt" value="" class="text-right"/>
                  <em class="won">원</em>
                </span>
              </div>
            </li>
            <li class="btn_wrap">
              <a href="javascript:;" class="btn" id="btn_search">조회</a>
            </li>
          </ul>
        </div>
        <div class="table_area">
					<div class="table_tot">
						<li class="text-right">
							<p style="font-size: 16px">총 <strong class="tot" style="color:blue !important; font-size: 16px"></strong>개</p>
						</li>
					</div>
          <table class="onetable">
            <colgroup>
              <col width="130px"/>
              <col width="150px"/>
              <col width="*" style="min-width:330px"/>
              <col width="130px"/>
              <col width="120px"/>
              <col width="120px"/>
              <col width="100px"/>
              <col width="120px"/>
              <col width="120px"/>
              <col width="120px"/>
              <col width="90px"/>
              <col width="130px"/>
            </colgroup>
            <thead>
              <th>개찰일자</th>
              <th>공고번호-차수</th>
              <th>공사명</th>
              <th>수요기관</th>
              <th>기초금액</th>
              <th>추정가격</th>
              <th>하한율</th>
              <th>A값</th>
              <th>순공사원가</th>
              <th>낙찰금액</th>
              <th>낙찰율</th>
              <th></th>
            </thead>
            <tbody id="list">
              <!--<tr>
                <td>2024-11-01</td>
                <td>2024000121-01</td>
                <td class="text-left">도시철도공사-건물공사</td>
                <td class="text-right">120,000,333</td>
                <td>87.745</td>
                <td class="text-right">67,900,112</td>
                <td class="text-right">89,000,333</td>
                <td class="text-right">89,000,333</td>
                <td>89%</td>
                <td>
                  <a href="javascript:;" class="btn btn_prediction" data-bs-toggle="modal" data-bs-target="#popupPrediction">예측</a>
                  <a href="javascript:;" class="btn bg-primary">URL</a>
                </td>
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


    <div class="modal fade" id="popupPrediction" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="popupPredictionLabel" aria-hidden="true">
      <div class="popup modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="popupPredictionLabel">입찰 예측</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <ul>
              <li>
                <label class="tit">공고번호-차수</label>
                <div class="input">
                  <input type="text" id="popupNo" name="popupNo" value=""/>
                </div>
              </li>
              <li>
                <label class="tit">공사명</label>
                <div class="input">
                  <input type="text" id="popupName" name="popupName" value=""/>
                </div>
              </li>
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
                  <em class="won">%</em>
                </div>
              </li>
              <li>
                <label class="tit">비고</label>
                <div class="input">
                  <input type="text" id="betc" name="betc" value=""/>
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
              <li>
                <label class="tit">예측 사정율</label>
                <div class="input cost readonly">
                  <input class="text-right" type="text" id="sbrate" name="sbrate" value="" readonly/>
                  <em class="won">%</em>
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
