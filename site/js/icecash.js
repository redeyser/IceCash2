
function showdoc(d){
    content=_getdata("/help?id="+d);
    doctext.innerHTML=content;
    doc.hidden=false;
}
function edit_user(iduser){
    ed_content=_getdata("/user?iduser="+iduser);
    ed_user.innerHTML="<div class='infoline center norm'> Редактирование пользователя</div>"+ed_content;
    ed_user.hidden=false;
}

function edit_sets(group){
    ed_content=_getdata("/sets_get?group="+group);
    ed_sets.innerHTML="<div class='infoline center norm'> Редактирование настроек</div>"+ed_content;
    ed_sets.hidden=false;
}

function edit_autosets(){
    ed_content=_getdata("/sets/autosets");
    ed_sets.innerHTML="<div class='infoline center norm'> Редактирование настроек</div>"+ed_content;
    ed_sets.hidden=false;
}

function ch_dev(v){
        ed_content=_getdata("/printer?idprinter="+v);
        if (ed_content!='0'){
            ed_drv.innerHTML="<div class='infoline center'> Подключение принтера </div>"+ed_content;
            ed_drv.hidden=false;
        }
}
function alert_message(head,content){
  message_content.innerHTML="<div class='infoline center'>"+head+"</div>"+content;
  message.hidden=false;
//  message_btn.focus();
}

function edit_drv(level){
    a=['dev','status','text']
    url=['printer','printer/status','printer/textlines']
    head=['Подключение принтера','Статус принтера','Текст в чеке']
    cur=a.indexOf(level)

    ed_content=_getdata(url[cur]);

    if (ed_content=='0'){
            alert_message('Ошибка','Драйвер принтеров не отвечает<br>Проверьте сервис DTPrint ');
            return;
    }
    if (ed_content.substr(0,1)==":"){
            alert_message('Ошибка драйвера',ed_content);
            return;
    }
    ed_drv.innerHTML="<div class='infoline center'>"+head[cur]+"</div>"+ed_content;
    ed_drv.hidden=false;
    return;
}

function cmd_autocreate(){
        result=_postdata("/cmd_autocreate",["printer"],["Fprint"]);
        if (result=="0"){
            message_content.innerHTML="<div class='infoline center'> Предупреждение </div>"+"Новые устройсва не найдены";
            message.hidden=false;
        }else{
            edit_drv("dev");
        }
}

function cmd_prn_setcurdatetime(){
        result=_postdata("/cmd/prn_setcurdatetime",["printer"],["Fprint"]);
        alert(result);
        if (result.substr(0,1)==":"){
                alert_message('Ошибка драйвера',result);
                return;
        }else{
            edit_drv("dev");
        }
}


