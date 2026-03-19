// ==========================================
// 초기값
const pagePerScreen = 100;
let pageNo = 1;
// ==========================================
// 1일~오늘날짜
const nowDate = (key) => {
  const ndate = new Date();
  const year = ndate.getFullYear();
  let month = ndate.getMonth() + 1;
  let day = ndate.getDate();

  if (month < 10) {
    month = "0" + month;
  }

  if (day < 10) {
    day = "0" + day;
  }

  if (key == 0) {
    return year + "-" + month + "-01";
  } else {
    return year + "-" + month + "-" + day;
  }
}
// ==========================================
// 조회
const btn_search = (cpage) => {
  const fdate = $("#fdate").val();
  const tdate = $("#tdate").val();
  const bkind = $("#bkind").val();
  const psize = pagePerScreen;

  const postData = { fdate, tdate, bkind, psize, cpage };

  $.ajax({
    url: "./ajax/svr_batch_List.php",
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
      const bkindObj = {
        1: "공고 API",
        2: "개찰 API",
        3: "예측모델생성"
      };

      if (tpage > 0) {
        const tag = list.map((el, idx) => `
        <tr>
          <td>${el.sdate}</td>
          <td>${el.edate}</td>
          <td>${bkindObj[el.bkind]}</td>
          <td>${el.pdate}</td>
          <td class="text-left">${el.bdesc !== null ? el.bdesc : ""}</td>
        </tr>`);

        $("#list").html(tag);

        pageNo = cpage;
        const shopListPageHtml = makePageNav(pagePerScreen, tpage, pageNo, "btn_search");
        $("#listPage").html(shopListPageHtml);
      } else {
        $("#list").html(`<tr>
          <td colspan="5" class="text-center">자료가 없습니다.</td>
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
$(function(){
  $('#gnb').find('ul').find('li').eq(2).addClass('active');
  // 날짜
  popdate("#fdate", 100, 100);
  popdate("#tdate", 100, 100);

  const f_fdate = getCookie("snsbid_batch_log_fdate") ? getCookie("snsbid_batch_log_fdate") : nowDate(0);
  const f_tdate = getCookie("snsbid_batch_log_tdate") ? getCookie("snsbid_batch_log_tdate") : nowDate(1);
  const f_bkind = getCookie("snsbid_batch_log_bkind") ? getCookie("snsbid_batch_log_bkind") : "-1";

  $('#fdate').val(f_fdate);
  $('#tdate').val(f_tdate);
  $('#bkind').val(f_bkind);

  $('#fdate').closest(".input").click(function(){
    $('#fdate').datepicker("show");
  });

  $('#fdate').change(function(){
    setCookie("snsbid_batch_log_fdate",$(this).val(),1);
  });

  $('#tdate').closest(".input").click(function(){
    $('#tdate').datepicker("show");
  });

  $('#tdate').change(function(){
    setCookie("snsbid_batch_log_tdate",$(this).val(),1);
  });

  $('#bkind').change(function(){
    setCookie("snsbid_batch_log_bkind",$(this).val(),1);
  });

  // 조회
  btn_search(1);

  // 조회 버튼
  $("#btn_search").on("click", function(e){
    e.preventDefault();

    btn_search(1);
  });
})
