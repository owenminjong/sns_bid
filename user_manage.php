<!DOCTYPE html>
<html lang="ko-KR">

<head>
  <?php include './inc/head.php'?>
  <script src="js/user_manage.js?v=<?=date("YmdHis")?>"></script>
  <style>
    .hide {display:none}
  </style>
</head>
<body id="user_manage">
  <?php include './inc/header.php'?>
  <div id="container">
    <div class="cont_inner">
        <div class="searchbox">
          <ul>
            <li>
              <label class="tit">이름</label>
              <div class="input">
                <input type="text" id="search_sfname" name="search_sfname" value=""/>
              </div>
            </li>
            <li>
              <label class="tit">아이디</label>
              <div class="input">
                <input type="text" id="search_sfid" name="search_sfid" value=""/>
              </div>
            </li>
            <li>
              <label class="tit">사용여부</label>
              <div class="select">
                <select id="search_isuse" name="search_isuse">
                  <option value="-1">::전체::</option>
                  <option value="1">사용</option>
                  <option value="0">사용안함</option>
                </select>
              </div>
            </li>
            <li class="btn_wrap">
              <a href="javascript:;" class="btn" id="btn_search">조회</a>
              <a href="javascript:;" class="btn bg-primary text-white" data-bs-toggle="modal" data-bs-target="#popupUser" id="btn_insert">신규 사용자</a>
            </li>
          </ul>
        </div>
        <div class="table_area">
          <table>
            <colgroup>
              <col width="100px"/>
              <col width="85px"/>
              <col width="140px"/>
              <col width="*"/>
              <col width="80px"/>
              <col width="150px"/>
            <colgroup>
            <thead>
              <th>이름</th>
              <th>관리자 여부</th>
              <th>전화번호</th>
              <th>아이디</th>
              <th>사용여부</th>
              <th>등록일자</th>
            </thead>
            <tbody id="list">
              <!--<tr>
                <td><a href="javascript" class="btn_link" data-bs-toggle="modal" data-bs-target="#popupUser">홍길동</a></td>
                <td>YES</td>
                <td>010-0000-0000</td>
                <td>bonobo</td>
                <td class="bg-primary2">사용</td>
                <td>2024-11-28 13:44</td>
              </tr>
              <tr>
                <td><a href="javascript" class="btn_link" data-bs-toggle="modal" data-bs-target="#popupUser">홍길동</a></td>
                <td>YES</td>
                <td>010-0000-0000</td>
                <td>bonobo</td>
                <td class="bg-greengray">사용안함</td>
                <td>2024-11-28 13:44</td>
              </tr>-->
            </tbody>
          </table>
        </div>

        <!--<nav class="pagnav">
          <ul class="pagination">
            <li class="page-item page_custom active">
              <a class="page-link" href="javascript:;"><span>1</span></a>
            </li>
            <li class="page-item page_custom">
              <a class="page-link" href="javascript:;"><span>2</span></a>
            </li>
            <li class="page-item page_custom">
              <a class="page-link" href="javascript:;"><span>3</span></a>
            </li>
          </ul>
        </nav>-->
    </div><!-- cont_inner -->


    <div class="modal fade" id="popupUser" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="popupUserLabel" aria-hidden="true">
      <div class="popup modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="popupUserLabel">
              사용자등록
              <!-- 신규등록일때는 '사용자등록', 조회일때는 '사용자관리'로 뜨도록 작업 부탁드립니다.-->
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <ul>
              <li>
                <label class="tit">이름</label>
                <div class="input">
                  <input type="text" id="sfname" name="sfname" value=""/>
                </div>
              </li>
              <li>
                <label class="tit">전화번호</label>
                <div class="input">
                  <input type="text" id="tel" name="tel" value=""/>
                </div>
              </li>
              <li>
                <label class="tit">아이디</label>
                <div class="input">
                  <input type="text" id="sfid" name="sfid" value=""/>
                </div>
              </li>
              <li>
                <label class="tit">비밀번호</label>
                <div class="input">
                  <input type="password" id="sfpw" name="sfpw" value=""/>
                </div>
              </li>
              <li>
                <label class="tit">비밀번호확인</label>
                <div class="input">
                  <input type="password" id="resfpw" name="resfpw" value=""/>
                </div>
              </li>
              <li>
                <label class="tit">관리자여부</label>
                <div class="select">
                  <select id="issvr" name="issvr">
                    <option value="1">YES</option>
                    <option value="0">NO</option>
                  </select>
                </div>
              </li>
              <li>
                <label class="tit">사용여부</label>
                <div class="select">
                  <select id="isuse" name="isuse">
                    <option value="1">사용</option>
                    <option value="0">사용안함</option>
                  </select>
                </div>
              </li>
            </ul>
          </div>
          <div class="modal-footer btn_wrap full-width text-right">
            <a href="javascript:;" class="btn btn_save bg-primary text-white" id="btn_save">저장</a>
            <a href="javascript:;" class="btn bg-red btn_delete hide" id="btn_del">삭제</a>
          </div>
        </div>
      </div>
    </div>

  </div><!-- container -->
  <?php include './inc/footer.php'?>
</body>
</html>
