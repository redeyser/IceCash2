#!/usr/bin/python
# -*- coding: utf-8

import datetime
import copy

"""
    Actions for IceServ
    License GPL
    writed by Romanenko Ruslan
    redeyser@gmail.com
"""

NO_FIND=-1
IF_PLACE_IN        = "IF_PLACE_IN"

IF_HEAD_PROPERTY   = "IF_HEAD_PROPERTY"
IF_GROUP_PROPERTY  = "IF_GROUP_PROPERTY"

DO_POS_CODE_IN     = "DO_POS_CODE_IN"
DO_POS_PROPERTY    = "DO_POS_PROPERTY"
DO_FILTERS_GROUP   = "DO_FILTERS_GROUP"

DO_HEAD_PROPERTY   = "DO_HEAD_PROPERTY"

DO_GROUP_SET_PROPERTY = "DO_GROUP_SET_PROPERTY"
DO_GROUP_DISCOUNT  = "DO_GROUP_DISCOUNT"
DO_GROUP_BONUS  = "DO_GROUP_BONUS"
DO_GROUP_DELETE    = "DO_GROUP_DELETE"

DO_GROUP_ADDPOS_PROPORCIONAL = "DO_GROUP_ADDPOS_PROPORCIONAL"
DO_SUMMA_ADDPOS_PROPORCIONAL = "DO_SUMMA_ADDPOS_PROPORCIONAL"
DO_GROUP_DIVPOS     = "DO_GROUP_DIVPOS"

DO_DENY_DISCOUNT_CARD = "DO_DENY_DISCOUNT_CARD"
DO_DENY_BONUS_CARD    = "DO_DENY_BONUS_CARD"
DO_DENY_BONUS_DISCOUNT= "DO_DENY_BONUS_DISCOUNT"

DO_SET_HEAD_DISCOUNT  = "DO_SET_HEAD_DISCOUNT"
DO_SET_HEAD_BONUS     = "DO_SET_HEAD_BONUS"

DO_PRIZE_GEN        = "DO_PRIZE_GEN"

class Actions:

    def __init__(self,db):
        self.db     = db

    def _read(self):
        tlists  = self.db._tlist_gets()
        self.tlists = {}
        self.filters = {}
        for t in tlists:
            if not self.tlists.has_key(t[0]):
                self.tlists[t[0]]=[]
            self.tlists[t[0]].append(str(t[1]))

        actions = self.db._actions_gets()
        self.actions=[]
        td=datetime.date.today()
        for a in actions:
            act = self.db.tb_actions_hd.result2values(a)
            dt1=act['dt1']
            dt2=act['dt2']
            wd =act['daysweek']
            if dt1 <= td and dt2 >=td:
                if wd[td.weekday()]=='1':
                    _if=self._prepare(act['_if'])
                    _then=self._prepare(act['_then'])
                    _sets=self._read_sets(_if)
                    self.actions.append({'name':act['name'],'_if':_if,'_then':_then,'sets':_sets})
        if len(self.actions)==0:
            return False
        #print self.actions
        return True

    def _prepare_line(self,p):
        self.parse_line={'cmd':'','list':[],'list_pref':'','var':'','dlist':''}
        if p=="" or p[0]=="#":
            return False
        arr=p.split(" ")
        self.parse_line['cmd']=arr[0]
            
        if self.parse_line['cmd'] == 'SET':
            try:
                self.parse_line['param']=arr[1]
                self.parse_line['value']=arr[2]
                return True
            except:
                self.parse_line['cmd']='ERROR'
                return False
        isnot=False
        isgroups=False
        for a in arr:
            if a=='NOT':
                isnot=True
            if a=='GROUPS':
                isgroups=True
            if a[0]=='{':
                if a[-1]!='}':
                    return False
                self.parse_line['var']=a[1:-1]
            if a[0]=='[':
                if a[-1]!=']':
                    return False
                self.parse_line['dlist']=a[1:-1].split(",")
            if a[0]=='(':
                if a[-1]!=')':
                    return False
                self.parse_line['list']=a[1:-1].split(",")
                if isgroups:
                    """ НОРМАЛИЗУЕМ СПИСОК ТОВАРОВ """
                    if self.parse_line['cmd'] in (DO_POS_CODE_IN):
                        l=[]
                        for n in self.parse_line['list']:
                            l+=self.tlists[n]
                        self.parse_line['list']=l
                if isnot:
                    self.parse_line['list_pref']='not'
                isnot=False
                isgroups=False

        #print "PARSE_line:", self.parse_line
        return True

    def _prepare_hash(self,h,s):
        params={}
        for l in h:
            a = l.split(s)
            if len(a)<2:
                continue
            params[a[0]]=a[1]
        return params

    def _prepare(self,p):
        arr=p.split("\r\n")
        #print "ARR",arr
        parse=[]
        for a in arr:
            if self._prepare_line(a):
                parse.append(self.parse_line)
        return parse

    def _read_sets(self,_if):
        """ ЧИТАЕМ ВСЕ НАСТРОЙКИ """
        sets={}
        for cmd in _if:
            if cmd['cmd']=='SET':
                sets[cmd['param']]=cmd['value']
        if not sets.has_key('BEFORE_CALC'):
            sets['BEFORE_CALC']='TRUE'
        return sets

    def _sets(self,act,key):
        """ ПОЛУЧИТЬ НАСТРОЙКУ """
        if act['sets'].has_key(key):
            return act['sets'][key]
        else:
            return None

    def _get_price_in_list(self,cmd):
        """ СЧИТАТЬ ВСЕ НОМЕНКЛАТУРНЫЕ ПОЗИЦИИ, УКАЗАННЫЕ В СПИСКЕ """
        #print cmd['list']
        self.db._price_get_in_list(",".join(cmd['list']))
        #print self.db.price

    def _code_in_list(self,pos,cmd):
        """ ПРОВЕРИТЬ ПРИНАДЛЕЖНОСТЬ ПОЗИЦИИ ЧЕКА К СПИСКУ УСЛОВИЯ """
        r=False
        for id in cmd['list']:
            #doom 17-02-27
            if id=='*' or self.db.price.has_key(id):
                if self.db.price[id]['istov']=='1':
                    #print pos['code'],id
                    if str(pos['code']) == id:
                        """ КОД ТОВАРА СОВПАЛ """
                        r=True
                        break
                else:
                    #print pos['p_idgroup'],id
                    if str(pos['p_idgroup']) == id:
                        """ КОД ГРУППЫ СОВПАЛ """
                        r=True
                        break
                        
        if cmd['list_pref']=='not':
            r=not r
        return r

    def _pos_property(self,var,_list):
        r=True
        for p in _list:
            a=p.split('?')
            if len(a)<3:
                return False
            (param,oper,val)=a
            #print pos[param],oper,val
            if not var.has_key(param):
                print "error param"
                return False
            if not oper in ("=","<",">",">=","<=","<>","in"):
                print "error operation"
                return False
            if type(var[param])==float:
                val=float(val)
            if type(var[param])==int:
                try:
                    val=int(val)
                except:
                    val=float(val)
            if oper=="=" and not var[param]==val:
                r=False
                break
            if oper=="<>" and not var[param]!=val:
                r=False
                break
            if oper==">" and not var[param]>val:
                r=False
                break
            if oper=="<" and not var[param]<val:
                r=False
                break
            if oper==">=" and not var[param]>=val:
                r=False
                break
            if oper=="<=" and not var[param]<=val:
                r=False
                break
            if oper=="in":
                arrlist=val.split(',')
                if not var[param] in arrlist:
                    r=False
                break
        return r
        
        
    def _do_if(self,act,ps):
        """ ПРОВЕРКА УСЛОВИЙ АКЦИИ """
        r=True
        self.filters={}
        positions=copy.deepcopy(ps)
        """ СНАЧАЛА ФОРМИРУЕМ ФИЛЬТРЫ И ГРУППИРОВКИ, ПОТОМ ПРОВЕРЯЕМ УСЛОВИЕ """
        for cmd in act['_then']:
            """ ----------- ФИЛЬТРУЕМ И ГРУППИРУЕМ ----------- """
            if cmd['cmd'] == DO_POS_CODE_IN:
                """ Предварительный фильтр """
                r=False
                """ ЗАГРУЖАЕМ НОМЕНКЛАТУРУ ИЗ УСЛОВИЯ"""
                self._get_price_in_list(cmd)
                """ Копируем все позиции в фильтр """
                if not self.filters.has_key(cmd['var']):
                    self.filters[cmd['var']]={'pos':[],'groups':{}}
                    posfilter=self.filters[cmd['var']]
                    for p in range(len(positions)):
                        posfilter['pos'].append(p)
                """ Исключаем из фильтра лишнее """
                posfilter=self.filters[cmd['var']]
                #print cmd['var'],"p",posfilter['pos']
                a=[]
                for p in posfilter['pos']:
                    pos=positions[p]
                    #print p,pos
                    if pos['storno']!=1:
                        if self._code_in_list(pos,cmd):
                            a.append(p)
                            r=True
                posfilter['pos']=a

            if cmd['cmd'] == DO_POS_PROPERTY:
                """ Фильтр по свойству ТОВАРА В ПОЗИЦИЯХ """
                r=False
                """ Копируем все позиции в фильтр """
                if not self.filters.has_key(cmd['var']):
                    self.filters[cmd['var']]={'pos':[],'groups':{}}
                    posfilter=self.filters[cmd['var']]
                    for p in range(len(positions)):
                        posfilter['pos'].append(p)
                """ Исключаем из фильтра лишнее """
                posfilter=self.filters[cmd['var']]
                #print cmd['var'],"p",posfilter['pos']
                a=[]
                for p in posfilter['pos']:
                    pos=positions[p]
                    #print p,pos
                    if pos['storno']!=1:
                        if self._pos_property(pos,cmd['list']):
                            a.append(p)
                            r=True
                posfilter['pos']=a

            if cmd['cmd'] == DO_FILTERS_GROUP:
                """ Группируем все фильтры """
                for k in self.filters.keys():
                    params={'paramf1':0,'paramf2':0,'paramf3':0,'discount':0,'bonus_discount':0,'bonus':0,'p_litrag':0}
                    for n in self.filters[k]['pos']:
                        for p in params:
                            params[p]+=positions[n][p]
                    params['count']=len(self.filters[k]['pos'])
                    if params['count']>0:
                        params['paramf1']=params['paramf1']/params['count']
                    self.filters[k]['groups']=params

        r=True
        for cmd in act['_if']:
            """ ---------------- ПРОВЕРЯЕМ УСЛОВИЯ --------------- """
            if cmd['cmd'] == IF_HEAD_PROPERTY:
                """ УСЛОВИЕ НА ЗАГОЛОВОК ЧЕКА """
                if not self._pos_property(self.db.ch_head,cmd['list']):
                    r=False
                    break

            if cmd['cmd'] == IF_GROUP_PROPERTY:
                """ УСЛОВИЕ НА ГРУППИРОВКУ """
                r=True
                if self.filters.has_key(cmd['var']):
                    posfilter=self.filters[cmd['var']]
                    if not self._pos_property(posfilter['groups'],cmd['list']):
                        r=False
                        break

        return r    

    def _do_then(self,act,ps):
        """ Действия Акции """
        r=True
        positions=ps
        for cmd in act['_then']:
            #if cmd['cmd'] == DO_HEAD_PROPERTY:
            #    """ ИСПРАВЛЕНИЕ ЗАГОЛОВОКА ЧЕКА """
            #    self.db._check_pos_upd(self.iduser,0,positions[p]['id'],{'dcount':positions[p]['paramf2']})
            #    self._pos_property(self.db.ch_head,cmd):
            #        r=False
            #        break

            if cmd['cmd'] == DO_GROUP_SET_PROPERTY:
                """ Меняем свойства товаров в группе """
                if self.filters.has_key(cmd['var']) and len(self.filters[cmd['var']]['pos'])>0:
                    sets=self._prepare_hash(cmd['dlist'],"=")
                    posfilter=self.filters[cmd['var']]
                    for p in posfilter['pos']:
                        self.db._check_pos_upd(self.iduser,0,positions[p]['id'],sets)

            if cmd['cmd'] == DO_GROUP_DELETE:
                """ Удаляем группу """
                if self.filters.has_key(cmd['var']) and len(self.filters[cmd['var']]['pos'])>0:
                    posfilter=self.filters[cmd['var']]
                    l=",".join([ "%d" % (positions[i]['id']) for i in posfilter['pos'] ])
                    self.db._check_pos_dels(self.iduser,0,l)

            if cmd['cmd'] == DO_GROUP_DISCOUNT:
                """ Устанавливаем скидку на группу """
                if self.filters.has_key(cmd['var']) and len(self.filters[cmd['var']]['pos'])>0:
                    posfilter=self.filters[cmd['var']]
                    #ds = self.db.ch_head['discount_sum']
                    #dg=posfilter['groups']['discount']
                    #dn=0
                    card=cmd['list'][0]
                    if not self.action_true:
                        proc=0
                        if self.db.ch_head['discount_card']==card:
                            self.db._check_update(self.iduser,0,{'discount_card':'','discount_proc':0})
                    else:
                        if self.db.ch_head['discount_card']=='':
                            self.db._check_update(self.iduser,0,{'discount_card':card,'discount_proc':0})
                        proc=cmd['list'][1]
                    if proc.find('sets.')!=-1:
                        proc=self.db.sets[proc[5:]]
                    for p in posfilter['pos']:
                        #print "pos",positions[p]['paramf2']
                        self.db._check_pos_upd(self.iduser,0,positions[p]['id'],{'discount_pos':proc})

            if cmd['cmd'] == DO_GROUP_BONUS:
                """ Устанавливаем бонус на группу """
                if self.filters.has_key(cmd['var']) and len(self.filters[cmd['var']]['pos'])>0:
                    posfilter=self.filters[cmd['var']]
                    if not self.action_true:
                        proc=cmd['list'][1]
                        if proc!='keep':
                            for p in posfilter['pos']:
                                self.db._check_pos_upd(self.iduser,0,positions[p]['id'],{'bonus_pos':0})
                    else:
                        if self.db.ch_head['bonus_card']!='':
                            proc=cmd['list'][0]
                            if proc.find('sets.')!=-1:
                                proc=self.db.sets[proc[5:]]
                            for p in posfilter['pos']:
                                self.db._check_pos_upd(self.iduser,0,positions[p]['id'],{'bonus_pos':proc})

            if cmd['cmd'] == DO_GROUP_ADDPOS_PROPORCIONAL:
                if not self.action_true:
                    continue
                """ Добавляем товар, пропорционально группировке, корректируем количество для бонусов """
                if self.filters.has_key(cmd['var']):
                    posfilter=self.filters[cmd['var']]
                    p2=posfilter['groups']['paramf2']
                    params=self._prepare_hash(cmd['list'],"=")
                    sets=self._prepare_hash(cmd['dlist'],"=")
                    #if p2>=float(params['gcount']):
                    n=p2//float(params['gcount'])
                    dcount=p2%float(params['gcount'])
                    add=float(params['count'])*n
                    if add!=0:
                        id=self.ch._add_tov(params['code'],add,setcur=False)
                        self.db._check_pos_upd(self.iduser,0,id,sets)
                    d=0
                    if n==0:
                        for p in posfilter['pos']:
                            #print "pos",positions[p]['paramf2']
                            self.db._check_pos_upd(self.iduser,0,positions[p]['id'],{'dcount':positions[p]['paramf2']})
                    else:
                        for p in posfilter['pos']:
                            if positions[p]['paramf2']>dcount-d:
                                positions[p]['dcount']=dcount-d
                                d=dcount
                            else:
                                positions[p]['dcount']=positions[p]['paramf2']
                                d=d+positions[p]['paramf2']
                            self.db._check_pos_upd(self.iduser,0,positions[p]['id'],{'dcount':positions[p]['dcount']})

            if cmd['cmd'] == DO_GROUP_DIVPOS:
                #if not self.action_true:
                #    continue
                """ Разделяем сгруппированный товар """
                if self.filters.has_key(cmd['var']):
                    posfilter=self.filters[cmd['var']]
                    p2=posfilter['groups']['paramf2']
                    params=self._prepare_hash(cmd['list'],"=")
                    sets=self._prepare_hash(cmd['dlist'],"=")
                    n=p2//float(params['count'])
                    dcount=p2%float(params['count'])
                    add=float(params['count'])*n
                    """ Удаляем группу """
                    setcur=False
                    if self.filters.has_key(cmd['var']) and len(self.filters[cmd['var']]['pos'])>0:
                        for i in posfilter['pos']:
                            if positions[i]['id']==self.db.ch_head['cursor']:
                                setcur=True
                        l=",".join([ "%d" % (positions[i]['id']) for i in posfilter['pos'] ])
                        self.db._check_pos_dels(self.iduser,0,l)

                    if add!=0:
                        id=self.ch._add_tov(params['code'],add,setcur=setcur)
                        self.db._check_pos_upd(self.iduser,0,id,sets)

                        #if sets.has_key('discount_pos'):
                        #    self.db._check_update(self.iduser,0,{'discount_card':cmd['var'],'discount_proc':0})
                        #else:
                        #    self.db._check_update(self.iduser,0,{'discount_card':'','discount_proc':0})
                        #self.ch._set("cursor",id)

                    if dcount!=0:
                        id=self.ch._add_tov(params['code'],dcount,setcur=setcur)
                        #self.ch._set("cursor",id)

            if cmd['cmd'] == DO_PRIZE_GEN:
                """ Генерировать приз в призовой системе """
                if not self.action_true:
                    self.db._check_update(self.iduser,0,{'idsystem':0,'idprize':0})
                    continue
                if self.db.ch_head['idsystem']==0 and len(cmd['list'])>0:
                    """ Помечаем чек как призовой """
                    idsystem=cmd['list'][0]
                    self.db._check_update(self.iduser,0,{'idsystem':idsystem,'idprize':0})

            if cmd['cmd'] == DO_SUMMA_ADDPOS_PROPORCIONAL:
                if not self.action_true:
                    continue
                """ Добавляем товар, пропорционально сумме чека """
                summa=self.db.ch_head['summa']
                params=self._prepare_hash(cmd['list'],"=")
                sets=self._prepare_hash(cmd['dlist'],"=")

                n=summa//float(params['summa'])
                add=float(params['count'])*n
                if add!=0:
                    id=self.ch._add_tov(params['code'],add,setcur=False)
                    self.db._check_pos_upd(self.iduser,0,id,sets)

            if cmd['cmd'] == DO_DENY_DISCOUNT_CARD:
                if not self.action_true:
                    continue
                self.db._check_update(self.iduser,0,{'discount_card':''})
                
            if cmd['cmd'] == DO_DENY_BONUS_CARD:
                if not self.action_true:
                    continue
                self.db._check_update(self.iduser,0,{'bonus_card':''})

            if cmd['cmd'] == DO_DENY_BONUS_DISCOUNT:
                if not self.action_true:
                    continue
                self.db._check_update(self.iduser,0,{'bonus_type':0})

            if cmd['cmd'] == DO_SET_HEAD_DISCOUNT:
                if len(cmd['list'])!=2:
                    continue
                (card,discount) = cmd['list']
                if discount.find('sets.')!=-1:
                    discount=self.db.sets[discount[5:]]

                if self.db.ch_head['discount_card'].find('DC')==-1 and self.db.ch_head['discount_card']!='':
                    continue

                if not self.action_true:
                    if card=='DCF':
                        self.db._check_update(self.iduser,0,{'discount_card':'','discount_proc':0})
                else:
                    self.db._check_update(self.iduser,0,{'discount_proc':discount,'discount_card':card,'fio':u'Автоматическая скидка'})

            if cmd['cmd'] == DO_SET_HEAD_BONUS:
                if len(cmd['list'])!=2:
                    continue
                bonus   = cmd['list'][0]
                default = cmd['list'][1]
                if not self.action_true:
                    if default!='keep' :
                    #and self.db.ch_head['bonus_proc']==float(bonus):
                        self.db._check_update(self.iduser,0,{'bonus_proc':default})
                else:
                    self.db._check_update(self.iduser,0,{'bonus_proc':bonus})
                                
        return r    

    def _do_before_calc(self,ch):
        self.iduser=ch.iduser
        self.ch=ch
        for act in self.actions:
            if self._sets(act,'BEFORE_CALC')=='TRUE':
                ch._pos_read()
                self.action_true = self._do_if(act,ch.pos)
                #print "Before.IF = ",self.action_true
                self._do_then(act,ch.pos)
                ch._docalc()
        return True

    def _do_after_calc(self,ch):
        self.iduser=ch.iduser
        self.ch=ch
        for act in self.actions:
            if self._sets(act,'AFTER_CALC')=='TRUE':
                ch._pos_read()
                self.action_true = self._do_if(act,ch.pos)
                #print "After.IF = ",self.action_true
                self._do_then(act,ch.pos)
        return True

    def _filter_before(self,idplace):
        self.f_actions=[]
        for act in self.actions:
            self._prepare(act['_if'])
            add=True
            for p in self.parse:
                print "PARSE_LINE",p
                if p['cmd']!=IF_PLACE_IN:
                    continue
                if p['list_type']=='groups':
                    place_in_list = False
                    for g in p['list']:
                        print g,self.gplaces[g]
                        if idplace in self.gplaces[g]:
                            place_in_list = True
                            break
                else:
                    place_in_list = str(idplace) in p['list']
                if not place_in_list and p['list_pref']=='':
                    add=False
                    break
                if place_in_list and p['list_pref']=='not':
                    add=False
                    break
            if add:
                a={'id':act['id'],'name':act['name'],'dt1':str(act['dt1']),'dt2':str(act['dt2']),'tm1':str(act['tm1']),'tm2':str(act['tm2']),'daysweek':act['daysweek'],'_if':act['_if'],'_then':act['_then']}
                self.f_actions.append(a)

        if len(self.f_actions)>0:
            return True
        else:
            return False


