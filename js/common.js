$(function(){

  $('.popup').find('.close').click(function(){
    $(this).parents('.popup').hide()
    $('.dimed').hide()
  })
  $('#img_popup').find('.close').click(function(){
    $(this).parents('#img_popup').hide()
    $('.dimed').hide()
  })

  // $( ".popup" ).draggable();

})

function loading_ani(val) {
  var $load = $('#load');
  if (val == true) {
    $load.css('display','block');
  } else if (val == false) {
    $load.css('display','none');
  }
}

function popdate(str, minN, maxN)
{
	var option = {
		changeYear: true,
		changeMonth: true,
		autoSize:true, 
		showMonthAfterYear:true, 
		dateFormat:"yy-mm-dd", 
		minDate: "-"+minN+"y",
		maxDate: "+"+maxN+"y",
		yearRange: "-100:+100",
		dayNames: ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"], 
		dayNamesMin:["일", "월", "화", "수", "목", "금", "토"], 
		monthNames:["- 01","- 02","- 03","- 04","- 05","- 06","- 07","- 08","- 09","- 10","- 11","- 12"],
		monthNamesShort: [ "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12" ],
		showButtonPanel:true,
		closeText:'Clear',
		onClose: function(dateText, inst) {
			if ($(window.event.srcElement).hasClass('ui-datepicker-close')) {
				document.getElementById(this.id).value = '';
			}
		}
	};

	$(""+str+"").datepicker(option);	
}

//날짜 입력 형식(yyyy-mm-dd) 체크. 2013-09-11 추가
function dateInputCheck(obj)
{
	var objValue=obj.value;
	var regExp=/^(19|20)\d{2}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[0-1])$/;

	if (objValue=="")
	{
		return;
	}

	if (!regExp.test(objValue))
	{
		alert("날짜형식은 yyyy-mm-dd 형식으로 입력하세요.");
		obj.value="";
		obj.focus();
	}
}

function hyphenAdd(txt,cnt)
{
	var txtLen;
	txtLen=txt.value.length;
	if (cnt==1)
	{
		if (txtLen==4)
		{
			txt.value=txt.value+"-";
		}
	}
	else if(cnt==2)
	{
		if (txtLen==4 || txtLen==9 || txtLen==14)
		{
			txt.value=txt.value+"-";
		}
	}
	else if(cnt==3)
	{
		if (txtLen==3 || txtLen==6)
		{
			txt.value=txt.value+"-";
		}
	}
	else if(cnt==4)
	{
		if (txtLen==4 || txtLen==7)
		{
			txt.value=txt.value+"-";
		}
	}
	
}

function makePageNav(page_per_screen, total_page, cur_page, func = "gotoPage") {
  var pageStr = "";

  if (total_page == 0) return pageStr;

  page_per_screen = parseInt(page_per_screen);
  total_page = parseInt(total_page);
  cur_page = parseInt(cur_page);

  var endpage = cur_page + (page_per_screen - (cur_page % page_per_screen));
  if (cur_page % page_per_screen == 0) endpage -= page_per_screen;

  var startpage = endpage - (page_per_screen - 1);

  if (endpage > total_page) endpage = total_page;

  if (cur_page <= page_per_screen) {
    //pageStr = `<li class="page-item page_custom"><a class="page-link"><i class="fa-solid fa-angles-left"></i></a></li>`;
    //pageStr += `<li class="page-item page_custom"><a class="page-link"><i class="fa-solid fa-angle-left"></i></a></li>`;
  } else {
    pageStr = `<li class="page-item page_custom"><a class="page-link" onclick="${func}(1)"><i class="fa-solid fa-angles-left"></i></a></li>`;
    pageStr += `<li class="page-item page_custom"><a class="page-link" onclick="${func}(${startpage - 1})"><i class="fa-solid fa-angle-left"></i></a></li>`;
  }

  for (var page = startpage; page <= endpage; page++) {
    if (page == cur_page) {
      pageStr += `<li class="page-item page_custom active">`;
      pageStr += `  <a class="page-link" href="javascript:;"><span>${page}</span></a>`;
      pageStr += `</li>`;
    } else {
      pageStr += `<li class="page-item page_custom">`;
      pageStr += `  <a class="page-link" href="javascript:;" onclick="${func}(${page})"><span>${page}</span></a>`;
      pageStr += `</li>`;
    }
  }

  if (endpage != total_page) {
    pageStr += `<li class="page-item page_custom"><a class="page-link" onclick="${func}(${endpage + 1})"><i class="fa-solid fa-angle-right"></i></a></li>`
    pageStr += `<li class="page-item page_custom"><a class="page-link" onclick="${func}(${total_page})"><i class="fa-solid fa-angles-right"></i></a></li>`
  } else {
    //pageStr += `<li class="page-item page_custom"><a class="page-link"><i class="fa-solid fa-angle-right"></i></a></li>`
    //pageStr += `<li class="page-item page_custom"><a class="page-link"><i class="fa-solid fa-angles-right"></i></a></li>`
  }

  return pageStr;
}

/***************************************************************************
 *  Cookie Write
 ***************************************************************************/
function setCookie(name,value,days) {
    var date, expires;
    if (days) {
        date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        expires = "; expires=" + date.toGMTString();
    }else{
        expires = "";
    }
    // document.cookie = name + "=" + value + expires + "; path=/";
    document.cookie = name + "=" + encodeURIComponent(value) + expires + "; path=/";
}

/***************************************************************************
 *  Cookie Read
 ***************************************************************************/
function getCookie(name) {
    var i, c, ca, nameEQ = name + "=";
    ca = document.cookie.split(';');
    for(i=0;i < ca.length;i++) {
        c = ca[i];
        while (c.charAt(0)==' ') {
            c = c.substring(1,c.length);
        }
        if (c.indexOf(nameEQ) == 0) {
            // return c.substring(nameEQ.length,c.length);
            return decodeURIComponent(c.substring(nameEQ.length,c.length));
        }
    }
    return '';
}

/***************************************************************************
 *  Cookie Delete
 ***************************************************************************/
function delCookie(name) {
    document.cookie = name + "=; path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;";
}