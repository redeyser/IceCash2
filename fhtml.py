#!/usr/bin/python
# -*- coding: utf-8

"""
    Functions html
"""
def ht_reptags_arr(html,amark,aval):
    for i in range(len(amark)):
        if aval[i]==None:
            aval[i]='None';
        html=html.replace(amark[i],aval[i])
    return html

def ht_reptags_hash(html,h):
    for key,val in h.items():
        k="%"+key+"%"
        if type(val)!=unicode:
            val=str(val)
        selected = "%"+key+"_"+val+"%"
        html=html.replace(k,val)
        html=html.replace(selected,"selected")
    return html

def ht_arrstr2select(arr,val):
    s=""
    for i in range(len(arr)):
        if arr[i]==val:
            ch='selected'
        else:
            ch=""
        s+="<option value='%s' %s >%s</option>\n" % (arr[i],ch,arr[i][:40])
    return s

def ht_arr2select(arr,val):
    s=""
    for i in range(len(arr)):
        if i==val:
            ch='selected'
        else:
            ch=""
        s+="<option value=%d %s >%s</option>\n" % (i,ch,arr[i])
    return s

def ht_arr2table(arr,tag,tr_on,tin_on):
    s=""
    for i in range(len(arr)):
        on=tr_on.replace("%id%",str(i))
        s+="<tr id='%s'><td %s><input type='text' \
        id='%s_%d' name='%s_%d' value='%s' %s /></td></tr>\n" % (tag,on,tag,i,tag,i,arr[i],tin_on)
    return s

def ht_db2select(records,field_id,field_val,val):
    s=""
    for record in records:
        if record[field_id]==val:
            ch='selected'
        else:
            ch=""
        s+="<option value='%s' %s >%s</option>\n" % (record[field_id],ch,record[field_val])
    return s

def ht_db2table(records,fields,idx,tr_on):
    s=""
    for record in records:
        id=record[idx]
        on=tr_on.replace("%id%",str(id))
        s+="<tr %s>" % on
        for field in fields:
            s+="<td>%s</td>" % record[field]
        s+="</tr>"
    return s

def ht_hash2table_input(h,caption,value):
    s=""
    for k,v in h.items():
        s+="<tr><td %s>%s</td><td><input %s name='%s' type='text' size=20 value='%s'/></td></tr>\n" % (caption,k,value,k,v)
    return s

