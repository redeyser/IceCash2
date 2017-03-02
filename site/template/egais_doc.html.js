init_data();
fill_form(TDATA_SETS_HD);
LAST_CT=0;
if (IDDOC!=0){
   async_get("/egais/get/doc?idd="+IDDOC,_fill_doc);
}
BTN_OSTAT=true;
DATA_DOC=[];// add from onclick ostat; -> show_content, show_content and head for ID_CURRENT!
function _fill_doc(t,p){
    var js=JSON.parse(t);
    var hd=js['hd'];
    DATA_DOC=js['ct'];
    DATA_FIELDS=js['fields'];
    _filldata(PREFIX_DATA,hd,[]);
    DATA_FIELDS[DATA_FIELDS.indexOf('pref_RegId')]='rst_InformARegId';
    DATA_FIELDS[DATA_FIELDS.indexOf('wbr_InformBRegId')]='rst_InformBRegId';
    DATA_FIELDS[DATA_FIELDS.indexOf('real_Quantity')]='rst_Quantity';
    DATA_FIELDS[DATA_FIELDS.indexOf('pref_ShortName')]='pref_FullName';
    LAST_CT=DATA_DOC.length;
    show_content();
}
function select_place(){
   var id=this.value;
   async_get("/egais/get/places?id="+id,show_place); 
}
function show_place(t,p){
    var js=JSON.parse(t);
    if (js['result']){
        data_recv_ShortName.value = js['data'][0]['description'];
    }

}
function init_data(){
    TDATA_SPRAV={};
    CLASS_ED="itext smallest";
    CLASS_MOD="but smallest";
    PREFIX_TD="tb_";
    PREFIX_MOD="mod_";
    PREFIX_DATA="data_";
    PREFIX_QUERY="";
    POSTFIX_QUERY="";
    QUERY_URL="/egais/doc/gets";
    TDATA_SETS_HD = {
        "recv_ShortName":  {"type":TYPE_TEXT,"size":40},   
        "recv_RegId"    :  {"type":TYPE_SP,   "all": false,    "query"     :"/egais/get/places"  ,"class":"flame","onchange":select_place },
        "wb_NUMBER"     :  {"type":TYPE_TEXT, "placeholder":"Номер","size":7},   
        "wb_Date"       :  {"type":TYPE_TEXT, "pattern"   :"20[1,2][0-9]-[0-1][0-9]-[0-3][0-9]","placeholder":"20YY-MM-DD","default":"curdate","size":8},   
        "wb_Type"       :  {"type":TYPE_LIST, "values"    :{"WBInvoiceFromMe":"Перемещение"} },   
        "wb_UnitType"   :  {"type":TYPE_LIST, "values"    :{"Packed":"Упаковка","Unpacked":"Без упаковки"} },   
        "status"        :  {"type":TYPE_LIST, "values"    :{1:"Новый",2:"Готовый"} }   
    }
    TDATA_LIST_OSTAT = {
        "pref_AlcCode"      :{"name":"Алкокод","class":"smallest"},   
        "oref_ShortName"    :{"name":"Поставщик","class":"smallest"},   
        "pref_FullName"     :{"name":"Производитель","class":"smallest"},   
        "pref_AlcVolume"    :{"name":"Градус","class":"smallest","grad":1,"fixed":2},   
        "pref_Capacity"     :{"name":"Литраж","class":"smallest","line":1},   
        "rst_InformBRegId"  :{"name":"Справка_B","class":"f70"},   
        "rst_InformARegId"  :{"name":"Справка_A","class":"f70","hidden":true},   
        "pref_ProductVCode" :{"name":"ID_RAR","class":"smallest"},   
        "rst_Quantity"      :{"name":"Количество","class":"smallest",'fixed':4},   
    }
}
function get_ostats(){
    if (BTN_OSTAT) { async_get("/egais/get/ostats",_get_ostats); btn_ostat.innerHTML='Документ';}
    else { tbdata.innerHTML='';show_content();   btn_ostat.innerHTML='Остатки';}
}

function _get_ostats(t,p){
  BTN_OSTAT=false;
  var js=JSON.parse(t);
  if (js['result']){
    TR_CLASS="smallest";
    var fd=js["fields"];
    var data=js["data"];
    var eltb=document.getElementById('tbdata');
    var _ct="";
    var one=false;
    for (var i in data) {
       var trid="ost_"+i;
       var r=data[i];
       var tr=create_line_content(TDATA_LIST_OSTAT,fd,trid,r);
       if (one){var cl='#808080';
       }else{var cl='#A0A0A0';}
       _ct+="<tbody style='background:"+cl+";'>"+tr+"</tbody>";
       one=!one;
    }
    eltb.innerHTML=_ct;
  }
  DATA_OSTAT=data;
  DATA_FIELDS=fd;
  setclick_ostat();
}
function setclick_ostat(){
    for (var i in DATA_OSTAT){
        var rc=DATA_OSTAT[i];
        var tr='ost_'+i;
        var eltr=document.getElementById(tr);
        eltr.addEventListener('click', ost_onclick, false);
    }
}
function ost_onclick(){
    var id=this.id.substr(4);
    if (confirm("Добавить эту позицию в документ?")){
        this.className='smallest warn';
        DATA_DOC.push(DATA_OSTAT[id]);
    }
}
function show_content(){
  BTN_OSTAT=true;
  
    TR_CLASS="smallest";
    var fd=DATA_FIELDS;
    var data=DATA_DOC;
    var eltb=document.getElementById('tbdata');
    var _ct="";
    var one=false;
    for (var i in data) {
       var trid="doc_"+i;
       var r=data[i];
       var tr=create_line_content(TDATA_LIST_OSTAT,fd,trid,r);
       if (one){var cl='#808080';
       }else{var cl='#A0A0A0';}
       _ct+="<tbody style='background:"+cl+";'>"+tr+"</tbody>";
       one=!one;
    }
    eltb.innerHTML=_ct;
    setclick_doc();
}
function setclick_doc(){
    for (var i in DATA_DOC){
        var rc=DATA_DOC[i];
        var tr='doc_'+i;
        var eltr=document.getElementById(tr);
        eltr.addEventListener('click', doc_onclick, false);
    }
}
function doc_onclick(){
    var id=this.id.substr(4);
    var i=DATA_FIELDS.indexOf('rst_Quantity');
    var k=DATA_DOC[id][i];
    var r=prompt("Введите количество:",k);
    if (r){  DATA_DOC[id][i]=parseFloat(r).toFixed(4); show_content(); }
}
function docsave(){
    var q=create_query(TDATA_SETS_HD,false,false);
    var dq = DATA_FIELDS.indexOf('rst_Quantity');
    var data=[];
    for (var i = LAST_CT; i<DATA_DOC.length;i++){
        data.push( [DATA_DOC[i][0],DATA_DOC[i][dq]] );
    }
    var jsh=JSON.stringify(q);
    var jsc=JSON.stringify(data);
    async_post('/egais/put/doc',{"id":IDDOC,"hd":jsh,"ct":jsc},_docsave);
}
function _docsave(t,p){
  var js=JSON.parse(t);
  if (js['result']){
    doc_cont.hidden=true;   
 }
}
