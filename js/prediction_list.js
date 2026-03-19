// ==========================================
// 초기값
const pagePerScreen = 100;
let pageNo = 1;
// ==========================================
// 오늘날짜-7일~오늘날짜
const nowDate = (key) => {
  const ndate = new Date();
  if (key == 0) {
    ndate.setDate(ndate.getDate() - 7);
  }
  const year = ndate.getFullYear();
  let month = ndate.getMonth() + 1;
  let day = ndate.getDate();

  if (month < 10) {
    month = "0" + month;
  }

  if (day < 10) {
    day = "0" + day;
  }

  return year + "-" + month + "-" + day;
}
// ==========================================
// 조회
const btn_search = (cpage) => {
  const fdate = $("#fdate").val();
  const tdate = $("#tdate").val();
  const bidNtceNo = $("#bidNtceNo").val();
  const bidNtceNm = $("#bidNtceNm").val();
  const comp = $("#comp").val();
  const psize = pagePerScreen;

  const postData = { fdate, tdate, bidNtceNo, bidNtceNm, comp, psize, cpage };

  $.ajax({
    url: "./ajax/bid_predict_List2.php",
    data: postData,
    type: "POST",
    dataType: "json",
    beforeSend: function () {
      loading_ani(true);
    },
    complete: function () {
      loading_ani(false);
    },
    success: function (res) {
      const list = res.list;
      const trec = res.trec;
      const tpage = res.tpage;

      if (tpage > 0) {
/*
        const tag = list.map((el, idx) => `
        <tr>
          <td>${el.opengDt}${el.opengTm !== null ? " "+el.opengTm : ""}</td>
          <td>${el.regdate.split(' ')[0]}</td>
          <td>${el.bidNtceNo}</td>
          <td class="text-left oneline">${el.bidNtceNm}</td>
          <td class="text-right">${parseInt(el.bssamt).toLocaleString()}</td>
          <td class="text-right">${parseInt(el.Aamt).toLocaleString()}</td>
          <td class="text-right">${parseInt(el.realAmt).toLocaleString()}</td>
          <td class="text-right">${parseInt(el.preamt).toLocaleString()}</td>
          <td>${number_format3(el.preRate)}%</td>
          <td>${number_format4(el.preRate2)}%</td>
          <td class="text-left">${el.bidwinnrNm !== null ? el.bidwinnrNm : ""}</td>
          <td class="text-right">${parseInt(el.sucsfbidAmt).toLocaleString()}</td>
          <td>${number_format3(el.sucsfbidRate)}%</td>
          <td>${number_format4(el.inrate)}%</td>
          <td class="text-left">${el.sfname}</td>
          <td class="text-left">${el.betc !== null ? el.betc : ""}</td>
        </tr>`);
*/
        const tag = list.map((el, idx) => `
        <tr>
          <td>${el.opengDt}${el.opengTm !== null ? " "+el.opengTm : ""}</td>
          <td>${el.regdate.split(' ')[0]}</td>
          <td>${el.bidNtceNo}</td>
          <td class="text-left oneline"><a href="javascript:;" class="link_remarks" data-bs-toggle="modal" data-bs-target="#popupRemarks" data-key="${el.psn}">${el.bidNtceNm}</a></td>
          <td class="text-right">${parseInt(el.bssamt).toLocaleString()}</td>
          <td class="text-right">${parseInt(el.Aamt).toLocaleString()}</td>
          <td class="text-right">${parseInt(el.realAmt).toLocaleString()}</td>
          <td class="text-right">${parseInt(el.preamt).toLocaleString()}</td>
          <td>${number_format4(el.preRate2)}%</td>
          <td class="text-left">${el.bidwinnrNm !== null ? el.bidwinnrNm : ""}</td>
          <td class="text-right">${parseInt(el.sucsfbidAmt).toLocaleString()}</td>
          <td>${number_format4(el.inrate)}%</td>
          <td class="text-left">${el.sfname}</td>
          <td class="text-left">${el.betc !== null ? el.betc : ""}</td>
        </tr>`);

        $("#list").html(tag);

        pageNo = cpage;
        const shopListPageHtml = makePageNav(pagePerScreen, tpage, pageNo, "btn_search");
        $("#listPage").html(shopListPageHtml);
      } else {
        $("#list").html(`<tr>
          <td colspan="12" class="text-center">자료가 없습니다.</td>
        </tr>`);
        $("#listPage").html("");
      }
    }, // success
    error: function (res, status, error) {
      loading_ani(false);
      console.log(res);
      console.log(status);
      console.log(error);

      if (res.responseJSON != undefined) {
        const json = res.responseJSON;
        alert(json.msg);
      } else {
        alert("조회 중 오류가 발생했습니다");
      }
    } // error
  }); // $.ajax
}
function number_format3(val){
  let str = Math.round(val*1000)/1000;
  return str;
}
function number_format4(val){
  let str = Math.round(val*10000)/10000;
  return str;
}
$(function(){
  $('#gnb').find('ul').find('li').eq(1).addClass('active');
  // 날짜
  popdate("#fdate", 100, 100);
  popdate("#tdate", 100, 100);

  const f_fdate = getCookie("snsbid_tender_notice_fdate") ? getCookie("snsbid_tender_notice_fdate") : nowDate(0);
  const f_tdate = getCookie("snsbid_tender_notice_tdate") ? getCookie("snsbid_tender_notice_tdate") : nowDate(1);
  const f_bidNtceNo = getCookie("snsbid_prediction_list_bidNtceNo") ? getCookie("snsbid_prediction_list_bidNtceNo") : "";
  const f_bidNtceNm = getCookie("snsbid_prediction_list_bidNtceNm") ? getCookie("snsbid_prediction_list_bidNtceNm") : "";

  $('#fdate').val(f_fdate);
  $('#tdate').val(f_tdate);
  $('#bidNtceNo').val(f_bidNtceNo);
  $('#bidNtceNm').val(f_bidNtceNm);

  $('#fdate').closest(".input").click(function(){
    $('#fdate').datepicker("show");
  });

  $('#tdate').closest(".input").click(function(){
    $('#tdate').datepicker("show");
  });

  $("#bidNtceNo").keydown(function(e){
    if (e.keyCode === 13) {
      btn_search(1);
    }
  });

  $("#bidNtceNm").keydown(function(e){
    if (e.keyCode === 13) {
      btn_search(1);
    }
  });

  $("#bidNtceNo").change(function(){
    setCookie("snsbid_prediction_list_bidNtceNo",$(this).val(),1);
  });

  $("#bidNtceNm").change(function(){
    setCookie("snsbid_prediction_list_bidNtceNm",$(this).val(),1);
  });

  // 조회
  btn_search(1);

  // 조회 버튼
  $("#btn_search").on("click", function(e){
    e.preventDefault();

    btn_search(1);
  });

  // 목록 링크
  $(document).on("click", ".link_remarks", function(e){
    e.preventDefault();

    const name = $(this).text();
    const psn = $(this).attr("data-key");
    $("#popupRemarks").find("#popupName").val(name);
    $("#popupRemarks").find("#popupkey").val(psn);
  });

  // 비고 수정
  $("#popupRemarks").find(".close").click(function(e){
    e.preventDefault();

    $("#popupRemarks").find("#popupName").val("");
    $("#popupRemarks").find("#popupkey").val("");
    $("#popupRemarks").find("#betc").val("");
  });

  $(document).on("click", "#popupRemarks .btn_save", function(e){
    e.preventDefault();

    const psn = $("#popupRemarks").find("#popupkey").val();
    const betc = $("#popupRemarks").find("#betc").val();
    const errtext = 'bid_predict_etc_update, 오류가 발생하였습니다.';
    const sData = {
      'psn': psn,
      'betc': betc
    };

    if (psn == "" || psn.length == 0) {
      alert("없는 자료이거나 잘못된 자료입니다.");
      return false;
    }

    $.ajax({
      type: 'post',
      dataType: 'json',
      url: "./ajax/bid_predict_etc_update.php",
      data: sData,
      beforeSend: function() {
        loading_ani(true);
      },
      complete: function() {
        loading_ani(false);
      },
      success: function (data) {
        if (data.ret == "1") {
          alert("비고가 정상적으로 수정되었습니다.");
          btn_search($("#listPage").find(".active").text());
          $("#popupRemarks .btn-close").click();
        } else {
          alert(data.err);
        }
      },
      error: function (request, status, error) {
        loading_ani(false);
        console.log('code: ' + request.status + "\n" + 'message: ' + request.responseText + "\n" +
        'error: ' + error);
      }
    });
  });
})
