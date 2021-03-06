#coding:utf-8

import traceback

import datetime
import time
# Create your views here.
from django.core.paginator import Paginator, EmptyPage
from django.db import transaction
from mongoengine import Q
from rest_framework import viewsets
from bson.objectid import ObjectId
from mongoDoc.models import GroupEmailData, IMChatMessages, ProjectData, MergeFinanceData, CompanyCatData, ProjRemark, \
    WXChatdata, ProjectNews, ProjIndustryInfo
from mongoDoc.serializers import GroupEmailDataSerializer, IMChatMessagesSerializer, ProjectDataSerializer, \
    MergeFinanceDataSerializer, CompanyCatDataSerializer, ProjRemarkSerializer, WXChatdataSerializer, \
    ProjectNewsSerializer, ProjIndustryInfoSerializer
from utils.customClass import JSONResponse, InvestError, AppEventRateThrottle
from utils.util import SuccessResponse, InvestErrorResponse, ExceptionResponse, catchexcption, logexcption, \
    loginTokenIsAvailable

ChinaList = ['北京','上海','广东','浙江','江苏','天津','福建','湖北','湖南','四川','河北','山西','内蒙古',
             '辽宁','吉林','黑龙江','安徽','江西','山东','河南','广西','海南','重庆','贵州','云南','西藏',
             '陕西','甘肃','青海','宁夏','新疆','香港','澳门','台湾']
RoundList = ['尚未获投','种子轮','天使轮','Pre-A轮','A轮','A+轮','Pre-B轮','B轮','B+轮','C轮','C+轮','D轮',
             'D+轮','E轮','F轮-上市前','已上市','新三板','战略投资','已被收购','不明确']

class CompanyCatDataView(viewsets.ModelViewSet):
    queryset = CompanyCatData.objects.all()
    serializer_class = CompanyCatDataSerializer

    @loginTokenIsAvailable()
    def list(self, request, *args, **kwargs):
        try:
            p_cat_name = request.GET.get('p_cat_name')
            queryset = self.queryset
            if p_cat_name:
                queryset = queryset(p_cat_name__icontains=p_cat_name)
            count = queryset.count()
            serializer = self.serializer_class(queryset,many=True)
            return JSONResponse(SuccessResponse({'count':count,'data':serializer.data}))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable()
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                raise InvestError(2001, msg=serializer.error_messages)
            return JSONResponse(SuccessResponse(serializer.data))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))


class MergeFinanceDataView(viewsets.ModelViewSet):
    throttle_classes = (AppEventRateThrottle,)
    queryset = MergeFinanceData.objects.all()
    serializer_class = MergeFinanceDataSerializer
    filter_class = {'com_name': 'icontains',
                    'currency': 'in',
                    'date': 'startswith',
                    'invsest_with': 'in',
                    'round': 'in',
                    'merger_with': 'icontains',
                    'com_id':'in'}

    def filterqueryset(self, request, queryset):
        for key, method in self.filter_class.items():
            value = request.GET.get(key)
            if value:
                if method == 'in':
                    value = value.split(',')
                queryset = queryset.filter(**{'%s__%s' % (key, method): value})
        return queryset

    @loginTokenIsAvailable()
    def list(self, request, *args, **kwargs):
        try:
            page_size = request.GET.get('page_size')
            page_index = request.GET.get('page_index')  # 从第一页开始
            if not page_size:
                page_size = 10
            if not page_index:
                page_index = 1
            queryset = self.filterqueryset(request, self.queryset)
            sort = request.GET.get('sort')
            if sort not in ['True', 'true', True, 1, 'Yes', 'yes', 'YES', 'TRUE']:
                queryset = queryset.order_by('-date',)
            else:
                queryset = queryset.order_by('date',)
            try:
                count = queryset.count()
                queryset = Paginator(queryset, page_size)
                queryset = queryset.page(page_index)
            except EmptyPage:
                return JSONResponse(SuccessResponse({'count': 0, 'data': []}))
            serializer = self.serializer_class(queryset,many=True)
            return JSONResponse(SuccessResponse({'count':count,'data':serializer.data}))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable(['usersys.as_admin'])
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            if data['investormerge'] == 1:
                MergeFinanceData_qs = MergeFinanceData.objects.filter(invse_id=data['invse_id'])
                if MergeFinanceData_qs.count() > 0:
                    serializer = self.serializer_class(MergeFinanceData_qs.first(), data=data)
                else:
                    serializer = self.serializer_class(data=data)
            elif data['investormerge'] == 2:
                MergeFinanceData_qs = MergeFinanceData.objects.filter(merger_id=data['merger_id'])
                if MergeFinanceData_qs.count() > 0:
                    serializer = self.serializer_class(MergeFinanceData_qs.first(), data=data)
                else:
                    serializer = self.serializer_class(data=data)
            else:
                raise InvestError(8001, msg='未知的类型')
            if serializer.is_valid():
                event = serializer.save()
                proj = ProjectData.objects(com_id=data['com_id'])
                if proj.count() > 0:
                    proj = proj.first()
                    if event.investormerge == 1:
                        if proj.invse_date < event.date:
                            proj.update(invse_date=event.date)
                            proj.update(invse_detail_money=event.money)
                            proj.update(invse_round_id=event.round)
                    event.update(com_cat_name=proj.com_cat_name)
                    event.update(com_sub_cat_name=proj.com_sub_cat_name)
                    event.update(com_addr=proj.com_addr)
            else:
                raise InvestError(2001, msg=serializer.error_messages)
            return JSONResponse(SuccessResponse(serializer.data))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable(['usersys.as_admin'])
    def update(self, request, *args, **kwargs):
        try:
            id = request.GET.get('id')
            instance = self.queryset.get(id=ObjectId(id))
            proj = ProjectData.objects(com_id=instance.com_id).first()
            instance.update(com_cat_name=proj.com_cat_name)
            instance.update(com_sub_cat_name=proj.com_sub_cat_name)
            instance.update(com_addr=proj.com_addr)
            return JSONResponse(SuccessResponse(True))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))


    @loginTokenIsAvailable()
    def getCount(self,request, *args, **kwargs):
        try:
            type = request.GET.get('type')
            if type == 'com':
                result = self.companyCountByCat()
            elif type == 'evecat':
                result = self.eventCountByCat()
            elif type == 'everound':
                result = self.eventCountByRound()
            elif type == 'eveaddr':
                result = self.eventCountByAddress()
            else:
                raise InvestError(2007)
            return JSONResponse(SuccessResponse(result))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    def companyCountByCat(self):
        allCat = CompanyCatData.objects.all().filter(p_cat_name=None)
        countDic = {}
        for cat in allCat:
            count = ProjectData.objects.all().filter(com_cat_name=cat.cat_name).count()
            countDic[cat.cat_name] = count
        return countDic

    def eventCountByCat(self):
        allCat = CompanyCatData.objects.all().filter(p_cat_name=None)
        countDic = {}
        for cat in allCat:
            count = self.queryset.filter(com_cat_name=cat.cat_name).count()
            countDic[cat.cat_name] = count
        return countDic

    def eventCountByRound(self):
        timelist = ['2010','2011','2012','2013','2014','2015','2016','2017']
        countList = {}
        for year in timelist:
            qs = self.queryset.filter(date__startswith=year)
            countDic = {}
            for cat in RoundList:
                count = qs.filter(round=cat).count()
                countDic[cat] = count
            countList[year] = countDic
        return countList

    def eventCountByAddress(self):
        countDic = {}
        for cat in ChinaList:
            count = self.queryset.filter(com_addr=cat).count()
            countDic[cat] = count
        return countDic

class ProjectDataView(viewsets.ModelViewSet):
    throttle_classes = (AppEventRateThrottle,)
    queryset = ProjectData.objects.all()
    serializer_class = ProjectDataSerializer
    filter_class = {'com_id': 'in',
                    'com_name':'icontains',
                    'com_cat_name': 'in',
                    'com_sub_cat_name': 'in',
                    'com_fund_needs_name': 'in',
                    'invse_round_id': 'in',
                    'com_status': 'in',
                    'com_born_date':'startswith',}

    def filterqueryset(self, request, queryset):
        for key, method in self.filter_class.items():
            value = request.GET.get(key)
            if value:
                if method == 'in':
                    value = value.split(',')
                queryset = queryset.filter(**{'%s__%s' % (key, method): value})
        return queryset

    # @loginTokenIsAvailable()
    def list(self, request, *args, **kwargs):
        try:
            page_size = request.GET.get('page_size')
            page_index = request.GET.get('page_index')  # 从第一页开始
            if not page_size:
                page_size = 10
            if not page_index:
                page_index = 1
            queryset = self.filterqueryset(request, self.queryset)
            com_addr = request.GET.get('com_addr')
            if com_addr:
                com_addr = com_addr.split(',')
                if '其他' in com_addr:
                    queryset = queryset.filter(Q(com_addr__nin=ChinaList)|Q(com_addr__in=com_addr))
                else:
                    queryset = queryset(Q(com_addr__in=com_addr))
            sort = request.GET.get('sort')
            if sort not in ['True', 'true', True, 1, 'Yes', 'yes', 'YES', 'TRUE']:
                queryset = queryset.order_by('-com_id',)
            else:
                queryset = queryset.order_by('com_id',)
            count = queryset.count()
            try:
                queryset = Paginator(queryset, page_size)
                queryset = queryset.page(page_index)
            except EmptyPage:
                return JSONResponse(SuccessResponse({'count': 0, 'data': []}))
            serializer = self.serializer_class(queryset,many=True)
            return JSONResponse(SuccessResponse({'count':count,'data':serializer.data}))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable(['usersys.as_admin'])
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            com_qs = ProjectData.objects.filter(com_id=data['com_id'])
            if com_qs.count() > 0:
                serializer = self.serializer_class(com_qs.first(),data=data)
            else:
                serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                proj= serializer.save()
                event_qs = MergeFinanceData.objects.filter(com_id=proj.com_id)
                if event_qs.count():
                    event_qs.update(com_cat_name=proj.com_cat_name)
                    event_qs.update(com_sub_cat_name=proj.com_sub_cat_name)
                    event_qs.update(com_addr=proj.com_addr)
            else:
                raise InvestError(2001, msg=serializer.error_messages)
            return JSONResponse(SuccessResponse(serializer.data))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    # @loginTokenIsAvailable(['usersys.as_admin'])
    # def update(self, request, *args, **kwargs):
    #     try:
    #         data = request.data
    #         com_id = data.get('com_id')
    #         instance = self.queryset.get(com_id=com_id)
    #         serializer = self.serializer_class(instance, data=data)
    #         if serializer.is_valid():
    #             serializer.save()
    #         else:
    #             raise InvestError(2001, msg=serializer.error_messages)
    #         return JSONResponse(SuccessResponse(serializer.data))
    #     except InvestError as err:
    #         return JSONResponse(InvestErrorResponse(err))
    #     except Exception:
    #         catchexcption(request)
    #         return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

class ProjectIndustryInfoView(viewsets.ModelViewSet):
    throttle_classes = (AppEventRateThrottle,)
    queryset = ProjIndustryInfo.objects.all()
    serializer_class = ProjIndustryInfoSerializer



    @loginTokenIsAvailable()
    def retrieve(self, request, *args, **kwargs):
        try:
            com_id = request.GET.get('com_id', None)
            if not com_id:
                raise InvestError(2007, msg='com_id 不能为空')
            com_qs = self.queryset.filter(com_id=com_id)
            if com_qs.count() > 0:
                instance = com_qs.first()
                response = self.serializer_class(instance).data
            else:
                response = None
            return JSONResponse(SuccessResponse(response))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable(['usersys.as_admin'])
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            com_qs = ProjIndustryInfo.objects.filter(com_id=data['com_id'])
            if com_qs.count() > 0:
                serializer = self.serializer_class(com_qs.first(),data=data)
            else:
                serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                raise InvestError(2001, msg=serializer.error_messages)
            return JSONResponse(SuccessResponse(serializer.data))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))


class ProjectNewsView(viewsets.ModelViewSet):

    throttle_classes = (AppEventRateThrottle,)
    queryset = ProjectNews.objects.all()
    serializer_class = ProjectNewsSerializer
    filter_class = {'com_id': 'in', 'com_name':'icontains',}

    def filterqueryset(self, request, queryset):
        for key, method in self.filter_class.items():
            value = request.GET.get(key)
            if value:
                if method == 'in':
                    value = value.split(',')
                queryset = queryset.filter(**{'%s__%s' % (key, method): value})
        return queryset

    @loginTokenIsAvailable()
    def list(self, request, *args, **kwargs):
        try:
            page_size = request.GET.get('page_size')
            page_index = request.GET.get('page_index')  # 从第一页开始
            if not page_size:
                page_size = 10
            if not page_index:
                page_index = 1
            queryset = self.filterqueryset(request, self.queryset)
            queryset = queryset.order_by('-newsdate')
            try:
                count = queryset.count()
                queryset = Paginator(queryset, page_size)
                queryset = queryset.page(page_index)
            except EmptyPage:
                return JSONResponse(SuccessResponse({'count': 0, 'data': []}))
            serializer = self.serializer_class(queryset,many=True)
            return JSONResponse(SuccessResponse({'count':count,'data':serializer.data}))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable(['usersys.as_admin'])
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                raise InvestError(2001, msg=serializer.error_messages)
            return JSONResponse(SuccessResponse(serializer.data))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))




class ProjectRemarkView(viewsets.ModelViewSet):

    queryset = ProjRemark.objects.all()
    serializer_class = ProjRemarkSerializer

    filter_class = {'com_name': 'in',
                    'com_id': 'in',}

    def filterqueryset(self, request, queryset):
        for key, method in self.filter_class.items():
            value = request.GET.get(key)
            if value:
                if method == 'in':
                    value = value.split(',')
                queryset = queryset.filter(**{'%s__%s' % (key, method): value})
        return queryset

    @loginTokenIsAvailable()
    def list(self, request, *args, **kwargs):
        try:
            page_size = request.GET.get('page_size')
            page_index = request.GET.get('page_index')  # 从第一页开始
            if not page_size:
                page_size = 10
            if not page_index:
                page_index = 1
            queryset = self.filterqueryset(request,self.queryset)
            if request.user.has_perm('usersys.admin_getmongoprojremark'):
                queryset = queryset(datasource=request.user.datasource_id)
            else:
                queryset = queryset(createuser_id=request.user.id)
            try:
                count = queryset.count()
                queryset = Paginator(queryset, page_size)
                queryset = queryset.page(page_index)
            except EmptyPage:
                return JSONResponse(SuccessResponse({'count': 0, 'data': []}))
            serializer = self.serializer_class(queryset,many=True)
            return JSONResponse(SuccessResponse({'count':count,'data':serializer.data}))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable()
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            data['createuser_id'] = request.user.id
            data['datasource'] = request.user.datasource_id
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                raise InvestError(2001, msg=serializer.error_messages)
            return JSONResponse(SuccessResponse(serializer.data))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable()
    def update(self, request, *args, **kwargs):
        try:
            id = request.GET.get('id')
            instance = self.queryset.get(id=ObjectId(id))
            if instance.createuser_id == request.user.id:
                pass
            else:
                raise InvestError(2009)
            data = request.data
            data.pop('createuser_id',None)
            data.pop('datasource',None)
            serializer = self.serializer_class(instance,data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                raise InvestError(2001, msg=serializer.error_messages)
            return JSONResponse(SuccessResponse(serializer.data))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable()
    def destroy(self, request, *args, **kwargs):
        try:
            id = request.GET.get('id')
            instance = self.queryset.get(id=ObjectId(id))
            if instance.createuser_id == request.user.id:
                pass
            elif request.user.has_perm('usersys.admin_deletemongoprojremark'):
                pass
            else:
                raise InvestError(2009)
            instance.delete()
            return JSONResponse(SuccessResponse({'isDeleted':True}))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))




class GroupEmailDataView(viewsets.ModelViewSet):
    queryset = GroupEmailData.objects.all()
    serializer_class = GroupEmailDataSerializer

    @loginTokenIsAvailable()
    def list(self, request, *args, **kwargs):
        try:
            projtitle = request.GET.get('title')
            page_size = request.GET.get('page_size')
            page_index = request.GET.get('page_index')  # 从第一页开始
            if not page_size:
                page_size = 10
            if not page_index:
                page_index = 1
            queryset = self.queryset(datasource=request.user.datasource_id)
            sort = request.GET.get('sort')
            if projtitle:
                queryset = queryset(projtitle__icontains=projtitle)
            if sort not in ['True', 'true', True, 1, 'Yes', 'yes', 'YES', 'TRUE']:
                queryset = queryset.order_by('-savetime',)
            else:
                queryset = queryset.order_by('savetime',)
            try:
                count = queryset.count()
                queryset = Paginator(queryset, page_size)
                queryset = queryset.page(page_index)
            except EmptyPage:
                return JSONResponse(SuccessResponse({'count': 0, 'data': []}))
            serializer = self.serializer_class(queryset,many=True)
            return JSONResponse(SuccessResponse({'count':count,'data':serializer.data}))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))


class WXChatDataView(viewsets.ModelViewSet):
    queryset = WXChatdata.objects.all()
    serializer_class = WXChatdataSerializer

    @loginTokenIsAvailable()
    def list(self, request, *args, **kwargs):
        try:
            page_size = request.GET.get('page_size')
            page_index = request.GET.get('page_index')  # 从第一页开始
            isShow = request.GET.get('isShow',False)
            if isShow in ['True', 'true', True, 1, 'Yes', 'yes', 'YES', 'TRUE']:
                isShow = True
            else:
                isShow = False
                if not request.user.has_perm('usersys.admin_manageWXChatData'):
                    isShow = True
            if not page_size:
                page_size = 10
            if not page_index:
                page_index = 1
            queryset = self.queryset(isShow=isShow)
            sort = request.GET.get('sort')
            if sort not in ['True', 'true', True, 1, 'Yes', 'yes', 'YES', 'TRUE']:
                queryset = queryset.order_by('-createtime',)
            else:
                queryset = queryset.order_by('createtime',)
            try:
                count = queryset.count()
                queryset = Paginator(queryset, page_size)
                queryset = queryset.page(page_index)
            except EmptyPage:
                return JSONResponse(SuccessResponse({'count': 0, 'data': []}))
            serializer = self.serializer_class(queryset,many=True)
            return JSONResponse(SuccessResponse({'count':count,'data':serializer.data}))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

    @loginTokenIsAvailable(['usersys.admin_manageWXChatData'])
    def update(self, request, *args, **kwargs):
        try:
            id = request.GET.get('id')
            instance = self.queryset.get(id=ObjectId(id))
            with transaction.atomic():
                data = {}
                data['isShow'] = not instance.isShow
                serializer = self.serializer_class(instance, data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    raise InvestError(2001, msg=serializer.error_messages)
                return JSONResponse(SuccessResponse(serializer.data))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))


def saveSendEmailDataToMongo(data):
    serializer = GroupEmailDataSerializer(data=data)
    try:
        if serializer.is_valid():
            serializer.save()
        else:
            raise InvestError(2001,msg=serializer.error_messages)
    except Exception:
        logexcption()

def readSendEmailDataFromMongo():
    start = datetime.datetime.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
    qs = GroupEmailData.objects.filter(savetime__gt=start)
    return GroupEmailDataSerializer(qs,many=True).data


class IMChatMessagesView(viewsets.ModelViewSet):
    queryset = IMChatMessages.objects.all()
    serializer_class = IMChatMessagesSerializer

    @loginTokenIsAvailable()
    def list(self, request, *args, **kwargs):
        try:
            chatto = request.GET.get('to')
            chatfrom = str(request.user.id)
            page_size = request.GET.get('max_size')
            timestamp = request.GET.get('timestamp')
            if not page_size:
                page_size = 20
            if not timestamp:
                timestamp = int(time.time())*1000
            queryset = self.queryset(timestamp__lt=str(timestamp))
            sort = request.GET.get('sort')
            if chatto:
                queryset = queryset(Q(to=chatto, chatfrom=chatfrom)|Q(to=chatfrom, chatfrom=chatto))
            else:
                queryset = queryset(Q(chatfrom=chatfrom) | Q(to=chatfrom))
            if sort not in ['True', 'true', True, 1, 'Yes', 'yes', 'YES', 'TRUE']:
                queryset = queryset.order_by('-timestamp',)
            else:
                queryset = queryset.order_by('timestamp',)
            count = queryset.count()
            queryset = queryset[0:page_size]
            serializer = self.serializer_class(queryset,many=True)
            return JSONResponse(SuccessResponse({'count':count,'data':serializer.data}))
        except InvestError as err:
            return JSONResponse(InvestErrorResponse(err))
        except Exception:
            catchexcption(request)
            return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

def saveChatMessageDataToMongo(data):
    queryset = IMChatMessages.objects.all()
    if queryset(msg_id=data['msg_id']).count() > 0:
        pass
    else:
        serializer = IMChatMessagesSerializer(data=data)
        try:
            if serializer.is_valid():
                serializer.save()
            else:
                raise InvestError(2001, msg=serializer.error_messages)
        except Exception:
            logexcption()