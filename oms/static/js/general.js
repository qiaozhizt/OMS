//定义pgorderlist中的action   key value
var PO_ACTIONS = {
    PO_SHIPPING: 'SHIPPING',
    PO_COMMENTS: 'ADD COMMENTS'
}


//mm-dd hh:mm
//yyyy-mm-ddThh:mm:ssZ
function formateTime(date) {
    var f = date.split('T');
    var md = f[0].split('-');
    var g = f[1].split('Z');
    var xf = g[0].split(":");
    var order_date = md[1] + '-' + md[2] + ' ' + xf[0] + ':' + xf[1];
    return order_date;
}

function add(eye) {
    var eyes = '';
    if (eye <= 0) {
        return eye;

    } else {
        eyes = '+' + eye;
        return eyes;
    }
}

//yyyy-mm-dd hh:mm:ss
function longTime(date) {
    var t = date.split('T');

    var z = t[1].substring(0, t[1].lastIndexOf('.'));

    var longtime = t[0] + " " + z;

    return longtime;

}


//按照单号查询的公共方法
var responseValue = [];

function searchByNumber(number, url, sign) {//sign是个数字，在后台判断sign，if sign =1,根据ordertrackingreport查询，否则根据ordertrackingreportcs查询
    if (number == '' || number == null) {
        layer.msg('Please enter a order number', {time: 3000, icon: 7});
    } else {
        $.ajax({
            url: url,
            type: "POST",
            async: false,
            data: {
                "number": number,
                "sign": sign
            },
            success: function (arg) {
                responseValue = arg;
            }

        })
    }
}

//可选的每页展示的数量
var pagesize = [25, 30, 34];

function addCOMMENTS(ordernumber, ordertype, id, action_value, $this) {
    $('#remarks').val('');
    var index = layer.open({
        title: '修改备注',
        type: 1,
        area: '35%', //宽高
        content: $('#comments'),
        btn: ['SAVE', 'CANCEL'],
        success: function (e) {
            $.post("/oms/addComments/", {'id': id, 'is_f': '1', 'ordertype': ordertype}, function (res) {
                e.find("#remarks").val(res);
            });
        },
        yes: function () {
            var textarea = $('#remarks').val();
            $.ajax({
                url: "/oms/addComments/",
                type: 'POST',
                data: {
                    'order_number': ordernumber,
                    'ordertype': ordertype,
                    'id': id,
                    'action_value': action_value,
                    'textarea': textarea
                },
                success: function (arg) {
                    layer.close(index);
                    var res = JSON.parse(arg);
                    if (res.status == 'Success') {
                        layer.msg('Success...', {time: 3000, icon: 6});
                        if (ordertype == "OPOR") {
                            $("#id_comments").val(textarea);
                        } else {
                            var cmt_id = "#" + $this.data("cmt_info");
                            $(cmt_id).text(textarea);
                            $(cmt_id + '_p').text(textarea);
                            $(cmt_id + '_h').text(textarea);
                        }
                    } else {
                        layer.open({
                            title: 'Error',
                            content: arg,
                            time: 5000
                        });
                    }

                }
            })
        }
    })

}

