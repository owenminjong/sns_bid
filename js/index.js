$(function(){
  delCookie("snsbid_tender_notice_fdate");
  delCookie("snsbid_tender_notice_tdate");
  delCookie("snsbid_tender_notice_bidNtceNo");
  delCookie("snsbid_tender_notice_bidNtceNm");
  delCookie("snsbid_tender_notice_isopen");
  delCookie("snsbid_tender_notice_famt");
  delCookie("snsbid_tender_notice_tamt");

  delCookie("snsbid_prediction_list_bidNtceNo");
  delCookie("snsbid_prediction_list_bidNtceNm");

  delCookie("snsbid_batch_log_fdate");
  delCookie("snsbid_batch_log_tdate");
  delCookie("snsbid_batch_log_bkind");

  $("#id").keyup(function(e){
    if (e.keyCode === 13) {
      $("#pw").select().focus();
    }
  });
  $("#pw").keyup(function(e){
    if (e.keyCode === 13) {
      $(".btn-login").click();
    }
  });
  $(".btn-login").click(function(){
    const postData = {
      "sfid":$("#id").val(),
      "sfpw":$("#pw").val()
    };
    $.ajax({
      type: 'post',
      dataType: 'json',
      url: "./ajax/Staff_Login.php",
      data: postData,
      success: function (data) {
        if (data.ret && data.ret > 0) {
          location.href=data.link;
        } else {
          alert("없는 자료이거나 잘못된 자료입니다.");
        }
      },
      error: function (res, status, error) {
        console.log(res);
        console.log(status);
        console.log(error);

        if (res.responseJSON != undefined) {
          const json = res.responseJSON;
          alert(json.msg);
        } else {
          alert("오류가 발생했습니다");
        }
      }
    });
  });
});