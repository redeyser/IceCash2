TYPE_SP="sp";
TYPE_LIST="list";
TYPE_TEXT="text";
TDATA_SPRAV={};
TDATA_TYPES = {   "sp"     : "select", 
            "list"   : "select", 
            "text"   : "input" };

IFNUM = { "=" : "=", ">" : ">","<":"<",">=":">=","<=":"<=","IN":"В списке","NOT IN":"Не в списке" }
IFNUMC= { "=" : "=","LIKE":"Подобно","IN":"В списке","NOT IN":"Не в списке" }
function curdate(mod){
    if (mod=='-1'){ return ""; }
    cdt= new Date();
    maxday=new Date(cdt.getFullYear(),cdt.getMonth()+1,0).getDate();
    m=cdt.getMonth()+1;
    d=cdt.getDate();
    if (m.length==1){ m="0"+m;}
    if (d.length==1){ d="0"+d;}
    if (mod=='1'){ d="01"; }
    if (mod=='2'){ d=maxday; }
    if (mod=='3'){ m="01";d="01"; }
    if (mod=='4'){ m="12";d="31"; }
    return cdt.getFullYear()+"-"+m+"-"+d;
}
function chmod_date(){
    id=this.id.substr(5);
    elname=PREFIX_DATA+id;
    eled=document.getElementById(elname);
    eled.value=curdate(this.value);
}
function clmod_empty(){
    id=this.id.substr(5);
    elname=PREFIX_DATA+id;
    eled=document.getElementById(elname);
    //if (TDATA_SETS[id]['default']){
    //    eled.value=TDATA_SETS[id]['default'];
    //}else{
    eled.value="";
    //}
}
function fill_form(tdatasets){
    TDATA_SETS=tdatasets;
    for ( var i in tdatasets ){ fill_element(i); }
}
function fill_element(i){
    var tdset = TDATA_SETS[i];
    var elname=PREFIX_TD+i;
    var eltd=document.getElementById(elname);
    if (eltd==null){ return; }
    eltd.innerHTML="";

    if (tdset["mod"]){
        if (tdset["mod"].indexOf("date")!=-1){
           var elmod=document.createElement("select"); 
           elmod.className=CLASS_MOD;
           elmod.id=PREFIX_MOD+"D"+i;
           fill_list(elmod,{0:'Сегодня',1:'НачМес',2:'КонМес',3:'НачГод',4:'КонГод'},true);
           eltd.appendChild(elmod);
           elmod.addEventListener('change', chmod_date, false);
        }
        if (tdset["mod"].indexOf("empty")!=-1){
           var elmod=document.createElement("button"); 
           elmod.className=CLASS_BUT;
           elmod.id=PREFIX_MOD+"B"+i;
           elmod.innerHTML="X";
           eltd.appendChild(elmod);
           elmod.addEventListener('click', clmod_empty, false);
        }
        if (tdset["mod"].indexOf("ifnum")!=-1){
           var elmod=document.createElement("select"); 
           elmod.className=CLASS_MOD;
           elmod.id=PREFIX_MOD+"N"+i;
           fill_list(elmod,IFNUM,false);
           eltd.appendChild(elmod);
        }
        if (tdset["mod"].indexOf("ifnumc")!=-1){
           var elmod=document.createElement("select"); 
           elmod.className=CLASS_MOD;
           elmod.id=PREFIX_MOD+"N"+i;
           fill_list(elmod,IFNUMC,false);
           eltd.appendChild(elmod);
        }
    }

    var eled=document.createElement(TDATA_TYPES[tdset["type"]]);
    if (tdset["class"]){ _CLASS=tdset["class"];  } else { _CLASS=""; }
    eled.className = CLASS_ED + " "+ _CLASS;
    eltd.appendChild(eled);
    eled.id=PREFIX_DATA+i;
    eled.size=tdset["size"];

    if (tdset["type"]==TYPE_LIST){ fill_list(eled,tdset["values"],tdset["all"]); }
    if (tdset["type"]==TYPE_SP){
        var result = _getdata(PREFIX_QUERY+tdset["query"]+POSTFIX_QUERY);
        if (result.length>6){
            var js=JSON.parse(result);
            if (js["result"]){ 
                TDATA_SPRAV[tdset["query"]]=js["data"];
                fill_list_order(eled,js["data"],js["order"],tdset["all"]); }
        }
    }
    if (tdset["default"]){  
        if (tdset["default"]=="curdate"){   def=curdate();   }
        else {def=tdset["default"];}
        eled.value=def;  
    }
    if (tdset["placeholder"]){ eled.placeholder=tdset["placeholder"];   }
    if (tdset["pattern"]){  eled.pattern=tdset["pattern"];  }
    if (tdset["onchange"]){  
       eled.addEventListener('change', tdset["onchange"], false);
    }
}
function fill_list(obj,values,all){
    if (all){
       var option = document.createElement("option");
       option.text="";
       option.value="-1";
       obj.add(option);
    }
   for (var j in values){
       var option = document.createElement("option");
       option.text=values[j];
       option.value=j;
       obj.add(option);
   }
}
function fill_list_order(obj,values,order,all){
    if (all){
       var option = document.createElement("option");
       option.text="";
       option.value="-1";
       obj.add(option);
    }
   for (var j in order){
       var option = document.createElement("option");
       option.text=values[order[j]];
       option.value=order[j];
       obj.add(option);
   }
}
function create_query(tdatasets,with_empty,with_mode){
    var query={};
    TDATA_SETS=tdatasets;
    for ( var i in TDATA_SETS ){ 
        if (get_element(i)){
            var tdset=TDATA_SETS[i];
            if (with_mode){
            if ((tdset['mod'])&&((tdset["mod"].indexOf("ifnum")!=-1)||(tdset["mod"].indexOf("ifnumc")!=-1))){
                var elmodname=PREFIX_MOD+"N"+i;
                var elmod=document.getElementById(elmodname);
                var mod=elmod.value;
            }else {mod=null;}
            if (!with_empty){
                if ((TMP_DATA==-1)&&(TDATA_TYPES[tdset["type"]]=="select")){  continue;  }
                if (TMP_DATA=="") {  continue;  }
            }
            query[i]={ "value":TMP_DATA, "mod":mod  } 
            }else{
                query[i]=TMP_DATA;
            }
        } 
    }
    return query;
}
function get_element(i){
    var tdset = TDATA_SETS[i];
    var elname=PREFIX_DATA+i;
    var eled=document.getElementById(elname);
    if (eled==null){ return false; }
    TMP_DATA=eled.value;
    return true;
}
function create_line_head(sets){
    var s="<tr>";
    for (var f in sets){
        if (sets[f]['line']){
            s=s+"</tr><tr>";
        }
        var fname=sets[f]['name'];
        s+="<th>"+fname+"</th>";
    }
    return s+"</tr>";
}
function create_line_content(sets,fd,id,r){
    var s="<tr class='"+TR_CLASS+"' id='"+id+"'>";
    for (var f in sets){
        if (sets[f]['hidden']){
            continue;
        }
        if (sets[f]['line']){
            s=s+"</tr><tr class='"+TR_CLASS+"' >";
        }
        iddata=fd.indexOf(f);
        if (iddata==-1){ continue; }
        if (sets[f]['sp']){
            var value=TDATA_SPRAV[sets[f]['sp']][r[iddata]];
        }else{ value=r[iddata]; }
        if ((sets[f]['class'])&&(value!='0')){_class=sets[f]['class'];}else{_class='';}
        if (sets[f]['fixed']){
            value=parseFloat(value).toFixed(sets[f]['fixed']);
            _class+=" rtext";
        }
        if (sets[f]['grad']){
            value=value+"&deg";
        }
        if ((sets[f]['nonull'])&&(value==null)){  value='';  }
        if (sets[f]['span']){
            var span='colspan="'+sets[f]['span']+'"';
        }else{span=""}
        s+="<td "+span+" class='"+_class+"'>"+value+"</td>";
    }
    return s+"</tr>";
}
function create_line_content_hash(sets){
    var s="<tr class='"+TR_CLASS+"' id='"+id+"'>";
    for (var f in sets){
        var r=sets[f];
        if (sets[f]['line']){
            s=s+"</tr><tr class='"+TR_CLASS+"' >";
        }
        var value=r['value']; 
        if ((sets[f]['class'])&&(value!='0')){_class=sets[f]['class'];}else{_class='';}
        if (sets[f]['fixed']){
            value=parseFloat(value).toFixed(sets[f]['fixed']);
            _class+=" rtext";
        }
        if (sets[f]['span']){
            var span='colspan="'+sets[f]['span']+'"';
        }else{span=""}
        s+="<td "+span+" class='"+_class+"'>"+value+"</td>";
    }
    return s+"</tr>";
}
function create_line_head_content(sets,fd,id,r){
    var s="<tr class='"+TR_CLASS+"' id='"+id+"'>";
    for (var f in sets){
        if (sets[f]['line']){
            s=s+"</tr><tr class='"+TR_CLASS+"' >";
        }
        var iddata=fd.indexOf(f);
        if (iddata==-1){ continue; }
        if (sets[f]['sp']){
            var value=TDATA_SPRAV[sets[f]['sp']][r[iddata]];
        }else{ var value=r[iddata]; }
        var fname=sets[f]['name'];
        if ((sets[f]['class'])&&(value!='0')){_class=sets[f]['class'];}else{_class='';}
        if (sets[f]['fixed']){
            value=parseFloat(value).toFixed(sets[f]['fixed']);
            _class+=" rtext";
        }
        if (sets[f]['span']){
            var span='colspan="'+sets[f]['span']+'"';
        }else{span=""}
        s+="<th>"+fname+"</th><td "+span+" class='"+_class+"'>"+value+"</td>";
    }
    return s+"</tr>";
}
function clear_tdata_itog(itog){
    for (var f in itog){ itog[f]['value']=0;  }
}
function inc_tdata_itog(itog,fd,r){
    for (var f in itog){
        var iddata=fd.indexOf(f);
        if (f=='count'){  itog[f]['value']=itog[f]['value']+1;  }
        if (iddata==-1){ continue; }
        itog[f]['value']=itog[f]['value']+r[iddata];
    }
}

function _putfile(page) {
    var file = document.getElementById("file");
    file=file.files[0]
    if (!file) { return; }
    var xhr = new XMLHttpRequest();
    xhr.open("POST", page, false);
    var formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
    return xhr.responseText;
}

function _getdata(page){
    var xhrp = new XMLHttpRequest();
    xhrp.open('GET', page, false);
    xhrp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhrp.send();
        if (xhrp.status != 200) {
            alert( xhrp.status + ': ' + xhrp.statusText );
            return '#err';
        } else {
            return xhrp.responseText;
        }
        return '#err';
}

function async_get(page,funct){
    var xhrp = new XMLHttpRequest();
    xhrp.open('GET', page, true);
    xhrp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhrp.send();

    xhrp.onreadystatechange = function() { 
        if (xhrp.readyState != 4) return;
        // RECIEVED ...
        if (xhrp.status != 200) {
            // ERROR
        } else {
            // OK
            funct(xhrp.responseText,page);
        }
    }   
    // BEGIN
    // ...
}

function async_post(page,data,funct){
    var xhrp = new XMLHttpRequest();
    xhrp.open('POST', page, true);
    xhrp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

    var body="";
    for (var n in data) {
        var v=data[n];
        if (body.length>0){add="&";}else{add="";}
        body = body + add + n + "=" + encodeURIComponent(v);
    }

    xhrp.send(body)
    xhrp.onreadystatechange = function() { 
        if (xhrp.readyState != 4) return;
        // RECIEVED ...
        if (xhrp.status != 200) {
            // ERROR
        } else {
            // OK
            funct(xhrp.responseText,page);
        }
    }   
    // BEGIN
    // ...
}

function _postdata(page,a_params,a_values){
    var xhrp = new XMLHttpRequest();
    xhrp.open('POST', page, false);
    xhrp.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    body="";
    for(var i=0; i<a_params.length; i++) {
        n=a_params[i];
        v=a_values[i];
        if (body.length>0){add="&";}else{add="";}
        body = body + add + n + "=" + encodeURIComponent(v);
    }
    xhrp.send(body);
        if (xhrp.status != 200) {
            alert( xhrp.status + ': ' + xhrp.statusText );
            return '#err';
        } else {
            return xhrp.responseText;
        }
        return '#err';
}

function _relocate(page){
    window.location=page;
}
function _filldata(prefix,data,ignore){
    var loaded_data={};
    for (i in data){
        var elname=prefix+i;
        var el=document.getElementById(elname);
        if (el != null){
            if (ignore.indexOf(i)==-1){
                loaded_data[i]=data[i];
                el.value=data[i];
            }
            else{
                el.value='';
            }
        }
    }
    return loaded_data;
}
function _fillsprav(ld,elname){
    var el=document.getElementById(elname);
    el.length=0;
    for (d in ld){
        var option = document.createElement("option");
        option.text  = ld[d];
        option.value = d;
        el.add(option);
    }
}
function _loaddata(ld){
    var data={};
    for (var i in ld){
        var elname='d_'+i;
        var el=document.getElementById(elname);
        if (el != null){
            if (ld[i]!=el.value){
                data[i]=el.value;
            }
        }
    }
    return data;
}
function _data2table(ld,fd,ext){
    var result="";
    var id=0;
    for (var i in ld){
        id+=1;
        var tr="tbdata_"+i;
        var td="tbdata_"+i+"_id";
        result+="<tr id='"+tr+"'><td id='"+td+"'>"+id+"</td>";
        var rc=ld[i];
        for ( var f in fd ){
            field = fd[f];
            if (field in rc){
                td="tbdata_"+i+"_"+field;
                value=rc[field];
                if (field in ext){
                    text=ext[field][value];
                }else{ text=value; }
                result+="<td id='"+td+"'>"+text+"</td>";
            }
        }
        result+="</tr>";
    }
    return result;
}

function _get_template(template,elname){
    TEMPLATE_ELEMENT=elname;
    async_get('/template/'+template+'.html',show_template);
}

function show_template(t,p){
    THIS_PAGE=p;
    var content=document.getElementById(TEMPLATE_ELEMENT);
    content.innerHTML=t;
    content.hidden=false;
    if (typeof script != "undefined"){
        document.body.removeChild(script);
    }
    var script = document.createElement('script');
    script.src = p+'.js';
    document.body.appendChild(script);
    script.onload = function() {
    }
}

