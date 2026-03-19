$(function(){
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
            $(".btn_calculating_price").click();
        } else {
            addPercent(this, 3);
        }
    });
    // 하한율 끝

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
});

function loading_ani(val) {
    var $load=$('#load');
    if (val == true) {
        $('#popup_wrap').show();
        $load.show();
    } else if (val == false) {
        $('#popup_wrap').hide();
        $load.hide();
    }
}

function formReset() {
    $("#bcost").val("0");
    $("#acost").val("0");
    $("#nccost").val("0");
    $("#mrcost").val("0");
    $("#sbprice").val("");
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