// ==========================================
// 초기값
var g_sfcode = 0;
// ==========================================
// 조회
const StaffList = () => {
  const postData = {
    "sfname":$("#search_sfname").val(), "sfid":$("#search_sfid").val(),
    "isuse":$('#search_isuse option:selected').val()
  };
  $.ajax({
    type: 'post',
    dataType: 'json',
    url: "./ajax/Staff_List.php",
    data: postData,
    beforeSend: function () {
      loading_ani(true);
    },
    complete: function () {
      loading_ani(false);
    },
    success: function (data) {
      let tag = '';
      if (data.length > 0) {
        tag = data.map((el) => 
          `<tr>
             <td><a href="javascript" class="btn_link" data-bs-toggle="modal" data-bs-target="#popupUser" data-code="${el.sfcode}">${el.sfname}</a></td>
             <td>${el.issvr == "1" ? "YES" : "NO"}</td>
             <td>${el.tel}</td>
             <td>${el.sfid}</td>
             <td class="${el.isuse == "1" ? "bg-primary2" : "bg-greengray"}">${el.isuse == "1" ? "사용" : "사용안함"}</td>
             <td>${el.regdate}</td>
          </tr>`
        );
      } else {
        tag = `<tr><td colspan="6" class="text-center">자료가 없습니다.</td></tr>`;
      }
      $(`#list`).html(tag);
    },

    error: function (request, status, error) {
      alert("조회 중 오류가 발생했습니다.\n잠시 후 다시 실행주세요.");
      loading_ani(false);
      console.log(request);
      console.log(status);
      console.log(error);
    }
  });
}
// ==========================================
// 팝업데이터 리셋
const formreset = () => {
  g_sfcode = 0;
  $("#popupUserLabel").text("사용자등록");
  $("#sfname").val("");
  $("#tel").val("");
  $("#sfid").val("");
  $("#sfpw").val("");
  $("#resfpw").val("");
  $("#issvr option:first").prop("selected",true);
  $("#isuse option:first").prop("selected",true);
  $("#btn_del").addClass("hide");
}
// ==========================================
// 상세조회
const StaffRow = (sfcode) => {
  $("#popupUserLabel").text("사용자관리");
  const postData = {
    "sfcode":sfcode
  };
  $.ajax({
    type: 'post',
    dataType: 'json',
    url: "./ajax/Staff_Row.php",
    data: postData,
    success: function (data) {
      if (data.sfcode && data.sfcode > 0) {
        g_sfcode = sfcode;
        $("#sfname").val(data.sfname);
        $("#tel").val(data.tel);
        $("#sfid").val(data.sfid);
        $("#sfpw").val(data.sfpw2);
        $("#resfpw").val(data.sfpw2);
        $(`#issvr option[value="${data.issvr}"]`).prop("selected",true);
        $(`#isuse option[value="${data.isuse}"]`).prop("selected",true);
        $("#btn_del").removeClass("hide");
      } else {
        alert("없는 자료이거나 잘못된 자료입니다.");
        $("#popupUser").find(".btn-close").click();
      }
    },

    error: function (request, status, error) {
      alert("조회 중 오류가 발생했습니다.\n잠시 후 다시 실행주세요.");

      console.log(request);
      console.log(status);
      console.log(error);
    }
  });
}
// ==========================================
// 삭제
const StaffDelete = (sfcode) => {
  const postData = {
    "sfcode":sfcode
  };
  const ans = confirm("삭제하시겠습니까?");
  if (!ans) return;
  $.ajax({
    type: 'post',
    dataType: 'json',
    url: "./ajax/Staff_Delete.php",
    data: postData,
    success: function (data) {
      if (data.ret > 0) {
        alert("사용자 자료가 삭제되었습니다.");
        $("#popupUser").find(".btn-close").click();
        StaffList();
      }
    },

    error: function (request, status, error) {
      alert("삭제 중 오류가 발생했습니다.\n잠시 후 다시 실행주세요.");

      console.log(request);
      console.log(status);
      console.log(error);
    }
  });
}
$(function(){
  $('#gnb').find('ul').find('li').eq(3).addClass('active');
  // =============================================================
  // 조회
  StaffList();

  $("#btn_search").click(function(){
    StaffList();
  });
  // =============================================================
  // 상세조회
  $(document).on("click", "#list .btn_link", function(){
    let sfcode = $(this).attr("data-code");
    if (sfcode > 0) {
      StaffRow(sfcode);
    }
  });
  // =============================================================
  // 팝업 닫기
  $("#popupUser").find(".btn-close").click(function(){
    formreset();
  });
  // =============================================================
  // 저장
  $("#btn_save").click(function(){
    let linkText = "";
    let postData = "";
    let alertText = "";
    if (g_sfcode == 0) {
      linkText = "./ajax/Staff_Insert.php";
      postData = {
        "sfname": $("#sfname").val(),
        "tel": $("#tel").val(),
        "sfid": $("#sfid").val(),
        "sfpw": $("#sfpw").val(),
        "resfpw": $("#resfpw").val(),
        "issvr": $("#issvr option:selected").val(),
        "isuse": $("#isuse option:selected").val()
      };
      alertText = "사용자 자료가 저장되었습니다.";
    } else {
      linkText = "./ajax/Staff_Update.php";
      postData = {
        "sfcode": g_sfcode,
        "sfname": $("#sfname").val(),
        "tel": $("#tel").val(),
        "sfid": $("#sfid").val(),
        "sfpw": $("#sfpw").val(),
        "resfpw": $("#resfpw").val(),
        "issvr": $("#issvr option:selected").val(),
        "isuse": $("#isuse option:selected").val()
      };
      alertText = "사용자 자료가 변경되었습니다.";
    }
    $.ajax({
      url: linkText,
      data: postData,
      dataType: "json",
      type: "POST",
      beforeSend: function () {
        loading_ani(true);
      },
      complete: function () {
        loading_ani(false);
      },
      success: function (res) {
        // console.log(res);
        alert(alertText);
        $("#popupUser").find(".btn-close").click();
        StaffList();
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
          alert("오류가 발생했습니다");
        }
      } // error
    }); // $.ajax
  });
  // =============================================================
  // 삭제
  $("#btn_del").click(function(){
    StaffDelete(g_sfcode);
  });
})
