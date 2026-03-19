// ==========================================
// 초기값
const pagePerScreen = 100;
let pageNo = 1;
var g_bsn = 0;
// ==========================================
// 오늘날짜~+7일
const nowDate = (key) => {
  const ndate = new Date();
  if (key != 0) {
    ndate.setDate(ndate.getDate() + 7);
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
  const isopen = $("#isopen option:selected").val();
  const famt = $("#famt").val().replace(/,/g,"");
  const tamt = $("#tamt").val().replace(/,/g,"");
  const psize = pagePerScreen;

  const postData = { fdate, tdate, bidNtceNo, bidNtceNm, isopen, famt, tamt, psize, cpage };

  $.ajax({
    url: "./ajax/api_bid_List.php",
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
        const tag = list.map((el, idx) => `
        <tr class="pointer listLink list_${el.bsn}">
          <td>${el.opengDt}${el.opengTm !== null ? " "+el.opengTm : ""}</td>
          <td class="No">${el.bidNtceNo}-${el.bidNtceOrd}</td>
          <td class="text-left oneline Name">${el.bidNtceNm !== null ? el.bidNtceNm : ""}</td>
          <td class="text-left oneline">${el.dminsttNm !== null ? el.dminsttNm : ""}</td>
          <td class="text-right bcost">${parseInt(el.bssamt).toLocaleString()}</td>
          <td class="text-right">${parseInt(el.bdgtAmt).toLocaleString()}</td>
          <td class="mrcost">${Math.round(el.sucsfbidLwltRate*1000)/1000}%</td>
          <td class="text-right acost">${parseInt(el.Aamt).toLocaleString()}</td>
          <td class="text-right nccost">${parseInt(el.realAmt).toLocaleString()}</td>
          <td class="text-right">${parseInt(el.sucsfbidAmt).toLocaleString()}</td>
          <td>${Math.round(el.sucsfbidRate*1000)/1000}%</td>
          <td>
            <a href="javascript:;" class="btn btn_prediction" data-bs-toggle="modal" data-bs-target="#popupPrediction" data-code="${el.bsn}">예측</a>
            ${el.bidNtceDtlUrl ? `<a href="${el.bidNtceDtlUrl}" class="btn bg-primary" target="_blank">URL</a>` : ``}
          </td>
        </tr>`);

        $("#list").html(tag);
        $(".tot").text(parseInt(trec).toLocaleString());

        pageNo = cpage;
        const shopListPageHtml = makePageNav(pagePerScreen, tpage, pageNo, "btn_search");
        $("#listPage").html(shopListPageHtml);
      } else {
        $("#list").html(`<tr>
          <td colspan="10" class="text-center">자료가 없습니다.</td>
        </tr>`);
        $("#listPage").html("");
        $(".tot").text("0");
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
// ==========================================
// 입찰 예측 저장
const BidInsert = () => {
  $("#popupUserLabel").text("사용자관리");
  let bidNtceNo = $("#popupNo").val().split("-");
  const postData = {
    "bsn":g_bsn,
    "bidNtceNo":bidNtceNo[0],
    "bidNtceNm":$("#popupName").val(),
    "bssamt":$("#bcost").val().replace(/,/g,''),
    "Aamt":$("#acost").val().replace(/,/g,''),
    "realAmt":$("#nccost").val().replace(/,/g,''),
    "urate":$("#mrcost").val().replace(/,/g,''),
    "preamt":$("#sbprice").val().replace(/,/g,''),
    "betc":$("#betc").val()
  };
  $.ajax({
    type: "post",
    dataType: "json",
    url: "./ajax/bid_predict_insert2.php",
    data: postData,
    beforeSend: function () {
      loading_ani(true);
    },
    complete: function () {
      loading_ani(false);
    },
    success: function (data) {
      if (data.ret && data.ret > 0) {
        alert("예측 자료가 정상 저장되었습니다.");
        $("#popupPrediction").find(".btn-close").click();
      } else {
        alert("없는 자료이거나 잘못된 자료입니다.");
      }
    },

    error: function (request, status, error) {
      var json = request.responseJSON;
      if (json.ret < 0) {
        alert(json.msg);
      } else {
        alert("저장 중 오류가 발생했습니다.\n잠시 후 다시 실행주세요.");
      }
      loading_ani(false);
      console.log(request);
      console.log(status);
      console.log(error);
    }
  });
}
$(function(){
  $('#gnb').find('ul').find('li').eq(0).addClass('active');

  // 날짜
  popdate("#fdate", 100, 100);
  popdate("#tdate", 100, 100);

  const f_fdate = getCookie("snsbid_tender_notice_fdate") ? getCookie("snsbid_tender_notice_fdate") : nowDate(0);
  const f_tdate = getCookie("snsbid_tender_notice_tdate") ? getCookie("snsbid_tender_notice_tdate") : nowDate(1);
  const f_bidNtceNo = getCookie("snsbid_tender_notice_bidNtceNo") ? getCookie("snsbid_tender_notice_bidNtceNo") : "";
  const f_bidNtceNm = getCookie("snsbid_tender_notice_bidNtceNm") ? getCookie("snsbid_tender_notice_bidNtceNm") : "";
  const f_isopen = getCookie("snsbid_tender_notice_isopen") ? getCookie("snsbid_tender_notice_isopen") : "-1";
  const f_famt = getCookie("snsbid_tender_notice_famt") ? getCookie("snsbid_tender_notice_famt") : "";
  const f_tamt = getCookie("snsbid_tender_notice_tamt") ? getCookie("snsbid_tender_notice_tamt") : "";

  $('#fdate').val(f_fdate);
  $('#tdate').val(f_tdate);
  $('#bidNtceNo').val(f_bidNtceNo);
  $('#bidNtceNm').val(f_bidNtceNm);
  $('#isopen').val(f_isopen);
  $('#famt').val(f_famt);
  $('#tamt').val(f_tamt);

  setCookie("snsbid_tender_notice_fdate",f_fdate,1);
  setCookie("snsbid_tender_notice_tdate",f_tdate,1);

  $('#fdate').closest(".input").click(function(){
    $('#fdate').datepicker("show");
  });

  $('#fdate').change(function(){
    setCookie("snsbid_tender_notice_fdate",$(this).val(),1);
  });

  $('#tdate').closest(".input").click(function(){
    $('#tdate').datepicker("show");
  });

  $('#tdate').change(function(){
    setCookie("snsbid_tender_notice_tdate",$(this).val(),1);
  });

  $("#famt").click(function(){
    $(this).focus().select();
  });

  $("#famt").keyup(function(){
    addComma(this);
  });

  $("#tamt").click(function(){
    $(this).focus().select();
  });

  $("#tamt").keyup(function(){
    addComma(this);
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

  $("#famt").keydown(function(e){
    if (e.keyCode === 13) {
      btn_search(1);
    }
  });

  $("#tamt").keydown(function(e){
    if (e.keyCode === 13) {
      btn_search(1);
    }
  });

  $("#bidNtceNo").change(function(){
    setCookie("snsbid_tender_notice_bidNtceNo",$(this).val(),1);
  });

  $("#bidNtceNm").change(function(){
    setCookie("snsbid_tender_notice_bidNtceNm",$(this).val(),1);
  });

  $("#isopen").change(function(){
    setCookie("snsbid_tender_notice_isopen",$(this).val(),1);
  });

  $("#famt").change(function(){
    setCookie("snsbid_tender_notice_famt",$(this).val(),1);
  });

  $("#tamt").change(function(){
    setCookie("snsbid_tender_notice_tamt",$(this).val(),1);
  });

  // 조회
  btn_search(1);

  // 조회 버튼
  $("#btn_search").on("click", function(e){
    e.preventDefault();

    btn_search(1);
  });

  // 입찰 예측 팝업
  $(document).on("click", ".btn_prediction", function(e){
    e.preventDefault();
    const code = $(this).attr("data-code");
    const No = $(`.list_${code}`).find(".No").text();
    const Name = $(`.list_${code}`).find(".Name").text();
    const bcost = $(`.list_${code}`).find(".bcost").text();
    const acost = $(`.list_${code}`).find(".acost").text();
    const nccost = $(`.list_${code}`).find(".nccost").text();
    const mrcost = $(`.list_${code}`).find(".mrcost").text().replace(/%/g, '');
    $("#popupNo").val(No);
    $("#popupName").val(Name);
    $("#bcost").val(bcost);
    $("#acost").val(acost);
    $("#nccost").val(nccost);
    $("#mrcost").val(mrcost);
    g_bsn = code;
  });

  // 기초금액
  $("#bcost").click(function(){
    $(this).select().focus();
  });

  $("#bcost").keyup(function(e){
    if (e.keyCode === 13) {
      $("#acost").select().focus();
    } else {
      addComma(this);
    }
  });
  // 기초금액 끝

  // A값
  $("#acost").click(function(){
    $(this).select().focus();
  });

  $("#acost").keyup(function(e){
    if (e.keyCode === 13) {
      $("#nccost").select().focus();
    } else {
      addComma(this);
    }
  });
  // A값 끝

  // 순공사원가
  $("#nccost").click(function(){
    $(this).select().focus();
  });

  $("#nccost").keyup(function(e){
    if (e.keyCode === 13) {
      $("#mrcost").select().focus();
    } else {
      addComma(this);
    }
  });
  // 순공사원가 끝

  // 하한율
  $("#mrcost").click(function(){
    $(this).select().focus();
  });

  $("#mrcost").keyup(function(e){
    if (e.keyCode === 13) {
      $("#betc").select().focus();
    } else {
      addPercent(this, 3);
    }
  });
  // 하한율 끝

  // 비고
  $("#betc").click(function(){
    $(this).select().focus();
  });

  $("#betc").keyup(function(e){
    if (e.keyCode === 13) {
      $(".btn_calculating_price").click();
    }
  });
  // 비고 끝

  $(".btn_reset").click(function(){
    formReset();
  });

  $(".btn_calculating_price").click(function(){
      const errtext = 'predict_cal, 오류가 발생하였습니다.(python)';
      const sData = {
        'bcost': $('#bcost').val().replace(/,/g, ''),
        'acost': $('#acost').val().replace(/,/g, ''),
        'nccost': $('#nccost').val().replace(/,/g, ''),
        'mrcost': $('#mrcost').val().replace(/,/g, '')
      };

      if ($("#bcost").val() == "0" || $("#bcost").val().length == 0) {
        alert("기초금액을 입력하여 주시기 바랍니다.");
        $("#bcost").select().focus();
        return false;
      }

      if ($("#acost").val() == "0" || $("#acost").val().length == 0) {
        alert("A값을 입력하여 주시기 바랍니다.");
        $("#acost").select().focus();
        return false;
      }

      if ($("#mrcost").val() == "0" || $("#mrcost").val().length == 0) {
        alert("하한율을 입력하여 주시기 바랍니다.");
        $("#mrcost").select().focus();
        return false;
      }

      $.ajax({
          type: 'post',
          dataType: 'json',
          url: "./ajax/predict_cal.php",
          data: sData,
          beforeSend: function() {
            loading_ani(true);
          },
          complete: function() {
            loading_ani(false);
          },
          success: function (data) {
            if (data[0].body != "" && data[0].body !== null) {
              $("#sbprice").val(data[0].body.replace(/\B(?=(\d{3})+(?!\d))/g, ","));
              Get_InputRate_sp();
            } else {
              $("#sbprice").val("");
            }
          },
          error: function (request, status, error) {
            loading_ani(false);
            console.log('code: ' + request.status + "\n" + 'message: ' + request.responseText + "\n" +
            'error: ' + error);
          }
      });
  });

  // =============================================================
  // 입찰 예측 팝업 닫기
  $("#popupPrediction").find(".btn-close").click(function(){
    formResetV1();
  });

  // =============================================================
  // 입찰 예측 팝업 저장 버튼
  $("#popupPrediction").find(".btn_save").click(function(){
    BidInsert();
  });
})

function Get_InputRate_sp() {
  const errtext = 'Get_InputRate_sp, 오류가 발생하였습니다.';
  const sData = {
    "inpay":$("#sbprice").val().replace(/,/g,''),
    "bssamt":$("#bcost").val().replace(/,/g,''),
    "Aamt":$("#acost").val().replace(/,/g,''),
    "realAmt":$("#nccost").val().replace(/,/g,''),
    "sucRate":$("#mrcost").val().replace(/,/g,''),
    "plnprc":0
  };

  $.ajax({
      type: 'post',
      dataType: 'json',
      url: "./ajax/Get_InputRate_sp.php",
      data: sData,
      //beforeSend: function() {
      //  loading_ani(true);
      //},
      //complete: function() {
      //  loading_ani(false);
      //},
      success: function (data) {
        if (data.ret != "" && data.ret !== null) {
          addPercentV1("#sbrate", data.ret, 5);
        } else {
          $("#sbrate").val("");
        }
      },
      error: function (request, status, error) {
        //loading_ani(false);
        console.log('code: ' + request.status + "\n" + 'message: ' + request.responseText + "\n" +
        'error: ' + error);
      }
  });
}

function predict(){
  window.open("predict.php", "_blank", "width=285 height=295, menubar=no, toolbar=no");
}

function formReset() {
  const code = g_bsn;
  const No = $(`.list_${code}`).find(".No").text();
  const Name = $(`.list_${code}`).find(".Name").text();
  const bcost = $(`.list_${code}`).find(".bcost").text();
  const acost = $(`.list_${code}`).find(".acost").text();
  const nccost = $(`.list_${code}`).find(".nccost").text();
  const mrcost = $(`.list_${code}`).find(".mrcost").text().replace(/%/g, '');
  $("#popupNo").val(No);
  $("#popupName").val(Name);
  $("#bcost").val(bcost);
  $("#acost").val(acost);
  $("#nccost").val(nccost);
  $("#mrcost").val(mrcost);
  $("#betc").val("");
  $("#sbprice").val("");
  $("#sbrate").val("");
}

function formResetV1() {
  $("#popupNo").val("");
  $("#popupName").val("");
  $("#bcost").val("0");
  $("#acost").val("0");
  $("#nccost").val("0");
  $("#mrcost").val("0");
  $("#betc").val("");
  $("#sbprice").val("");
  $("#sbrate").val("");
  g_bsn = 0;
}

function addComma(e) {
  let ret = '';
  let fir = $(e).val().replace(/[^0-9]/g, '');
  ret = fir.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  $(e).val(ret);
}

function addPercent(element, decimalPlaces) {
  let value = $(element).val();

  // 소수점이 1개만 남도록 처리
  const parts = value.split('.');
  if (parts.length > 2) {
    value = parts[0] + '.' + parts[1];
  }

  // 소수점 자리수 초과 시 잘라내기
  if (parts[1] != null && (parts[1].length > decimalPlaces)) {
    let parts1 = "";
    parts1 = parts[1].substring(0, decimalPlaces);
    parts[1] = parts1;
  }

  // 숫자만 남기기, 천단위 콤마 추가 (소수점 앞부분만 처리)
  let integerPart = parts[0].replace(/[^0-9]/g, '');
  integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');

  // 숫자만 남기기 (소수점 뒷부분만 처리)
  const decimalPart = parts[1] != null ? '.' + parts[1].replace(/[^0-9]/g, '') : '';
  value = integerPart + decimalPart;

  // 입력 필드 업데이트
  $(element).val(value);
}

function addPercentV1(element, val, decimalPlaces) {
  let value = val;

  // 소수점이 1개만 남도록 처리
  const parts = value.split('.');
  if (parts.length > 2) {
    value = parts[0] + '.' + parts[1];
  }

  // 소수점 자리수 초과 시 잘라내기
  if (parts[1] != null && (parts[1].length > decimalPlaces)) {
    let parts1 = "";
    parts1 = parts[1].substring(0, decimalPlaces);
    parts[1] = parts1;
  }

  // 숫자만 남기기, 천단위 콤마 추가 (소수점 앞부분만 처리)
  let integerPart = parts[0].replace(/[^0-9]/g, '');
  integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');

  // 숫자만 남기기 (소수점 뒷부분만 처리)
  const decimalPart = parts[1] != null ? '.' + parts[1].replace(/[^0-9]/g, '') : '';
  value = integerPart + decimalPart;

  // 입력 필드 업데이트
  $(element).val(value);
}