#coding=utf-8
import traceback
from django.core.paginator import Paginator, EmptyPage
from django.db import models,transaction
from django.db.models import Q,QuerySet
from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.reverse_related import ForeignObjectRel
from guardian.shortcuts import assign_perm
from rest_framework import filters
from rest_framework import viewsets
import datetime
from proj.models import project, finance, projectTags, projectIndustries, projectTransactionType, favoriteProject
from proj.serializer import ProjSerializer, FinanceSerializer, ProjCreatSerializer, \
    ProjCommonSerializer, FinanceChangeSerializer, FinanceCreateSerializer, FavoriteSerializer
from sourcetype.models import Tag, Industry, TransactionType
from usersys.models import MyUser
from utils.util import catchexcption, read_from_cache, write_to_cache, loginTokenIsAvailable, returnListChangeToLanguage, \
    returnDictChangeToLanguage
from utils.myClass import JSONResponse, InvestError


class ProjectView(viewsets.ModelViewSet):
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend,)
    queryset = project.objects.all().filter(is_deleted=False)
    filter_fields = ('titleC', 'titleE','isoverseasproject')
    serializer_class = ProjSerializer
    redis_key = 'project'
    Model = project

    def get_queryset(self):
        if self.request.user.is_anonymous:
            raise InvestError(code=8889)
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.filter(datasource=self.request.user.datasource)
        else:
            raise InvestError(code=8890)
        return queryset

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )
        obj = read_from_cache(self.redis_key + '_%s' % self.kwargs[lookup_url_kwarg])
        if not obj:
            try:
                obj = self.Model.objects.get(id=self.kwargs[lookup_url_kwarg], is_deleted=False)
            except self.Model.DoesNotExist:
                raise InvestError(code=4002,msg='proj with this "%s" is not exist' % self.kwargs[lookup_url_kwarg])
            else:
                write_to_cache(self.redis_key + '_%s' % self.kwargs[lookup_url_kwarg], obj)
        if obj.datasource != self.request.user.datasource:
            raise InvestError(code=8888,msg='资源非同源')
        return obj

    def list(self, request, *args, **kwargs):
        page_size = request.GET.get('page_size')
        page_index = request.GET.get('page_index')  # 从第一页开始
        lang = request.GET.get('lang')
        if not page_size:
            page_size = 10
        if not page_index:
            page_index = 1
        queryset = self.filter_queryset(self.get_queryset())
        if request.user.is_anonymous:
            queryset = queryset.filter(isHidden=False)
        else:
            if request.user.has_perm('proj.admin_getproj'):
                queryset = queryset
            else:
                queryset = queryset.filter(Q(isHidden=False) | Q(createuser=request.user))
        try:
            queryset = Paginator(queryset, page_size)
        except EmptyPage:
            return JSONResponse({'success': True, 'result': [], 'errorcode': 1000, 'errormsg': None})
        queryset = queryset.page(page_index)
        serializer = ProjCommonSerializer(queryset, many=True)
        return JSONResponse({'success': True, 'result': returnListChangeToLanguage(serializer.data,lang), 'errorcode': 1000, 'errormsg': None})


    @loginTokenIsAvailable(['proj.admin_addproj','proj.user_addproj'])
    def create(self, request, *args, **kwargs):
        try:
            projdata = request.data
            lang = request.GET.get('lang')
            projdata['createuser'] = request.user.id
            tagsdata = projdata.pop('tags',None)
            industrydata = projdata.pop('industries',None)
            transactiontypedata = projdata.pop('transactionType',None)
            with transaction.atomic():
                proj = ProjCreatSerializer(data=projdata)
                if proj.is_valid():
                    pro = proj.save()
                    if tagsdata:
                        tagslist = []
                        for transactionPhase in tagsdata:
                            tagslist.append(projectTags(proj=pro, tag_id=transactionPhase,createuser=request.user))
                        pro.project_tags.bulk_create(tagslist)
                    if industrydata:
                        industrylist = []
                        for transactionPhase in industrydata:
                            industrylist.append(projectIndustries(proj=pro, industry_id=transactionPhase,createuser=request.user))
                        pro.project_industries.bulk_create(industrylist)
                    if transactiontypedata:
                        transactiontypelist = []
                        for transactionPhase in tagsdata:
                            transactiontypelist.append(projectTransactionType(proj=pro, transactionType_id=transactionPhase,createuser=request.user))
                        pro.project_TransactionTypes.bulk_create(transactiontypelist)
                else:
                    raise InvestError(code=4001,
                                          msg='data有误_%s\n%s' % (proj.error_messages, proj.errors))

                assign_perm('proj.user_changeproj', request.user, pro)
                assign_perm('proj.user_deleteproj', request.user, pro)
                assign_perm('proj.user_getproj', request.user, pro)
                return JSONResponse({'success':True,'result': returnDictChangeToLanguage(ProjSerializer(pro).data,lang),'errorcode':1000,'errormsg':None})
        except InvestError as err:
            return JSONResponse({'success': False, 'result': None, 'errorcode': err.code, 'errormsg': err.msg})
        except Exception:
            catchexcption(request)
            return JSONResponse({'success': False, 'result': None, 'errorcode': 9999,
                                 'errormsg': traceback.format_exc().split('\n')[-2]})

    @loginTokenIsAvailable()
    def retrieve(self, request, *args, **kwargs):
        try:
            lang = request.GET.get('lang')
            if request.user.has_perm('proj.admin_getproj'):
                serializerclass = ProjSerializer
            else:
                serializerclass = ProjSerializer
            instance = self.get_object()
            if instance.isHidden:
                if not request.user.has_perm('proj.user_getproj', instance) or not request.user.has_perm(
                        'proj.admin_getproj'):
                    raise InvestError(code=4004, msg='没有权限查看隐藏项目')
            serializer = serializerclass(instance)
            return JSONResponse({'success': True, 'result': returnDictChangeToLanguage(serializer.data,lang), 'errorcode': 1000, 'errormsg': None})
        except InvestError as err:
            return JSONResponse({'success': False, 'result': None, 'errorcode': err.code, 'errormsg': err.msg})
        except Exception:
            catchexcption(request)
            return JSONResponse({'success': False, 'result': None, 'errorcode': 9999,
                                 'errormsg': traceback.format_exc().split('\n')[-2]})
    @loginTokenIsAvailable()
    def update(self, request, *args, **kwargs):
        try:
            pro = self.get_object()
            lang = request.GET.get('lang')
            if request.user.has_perm('proj.admin_changeproj'):
                pass
            elif request.user.has_perm('proj.user_changeproj',pro):
                pass
            else:
                raise InvestError(code=2009,msg='非上传方或管理员无法修改项目')
            projdata = request.data
            projdata['lastmodifyuser'] = request.user.id
            projdata['lastmodifytime'] = datetime.datetime.now()
            tagsdata = projdata.pop('tags', None)
            industrydata = projdata.pop('industries', None)
            transactiontypedata = projdata.pop('transactionType', None)
            with transaction.atomic():
                proj = ProjCreatSerializer(data=projdata)
                if proj.is_valid():
                    pro = proj.save()
                    if tagsdata:
                        taglist = Tag.objects.in_bulk(tagsdata)
                        addlist = [item for item in taglist if item not in pro.tags.all()]
                        removelist = [item for item in pro.tags.all() if item not in taglist]
                        pro.project_tags.filter(tag__in=removelist, is_deleted=False).update(is_deleted=True,
                                                                                           deletedtime=datetime.datetime.now(),
                                                                                           deleteduser=request.user)
                        usertaglist = []
                        for tag in addlist:
                            usertaglist.append(projectTags(proj=pro, tag=tag, createuser=request.user))
                        pro.project_tags.bulk_create(usertaglist)

                    if industrydata:
                        industrylist = Industry.objects.in_bulk(industrydata)
                        addlist = [item for item in industrylist if item not in pro.industries.all()]
                        removelist = [item for item in pro.industries.all() if item not in industrylist]
                        pro.project_industries.filter(industry__in=removelist, is_deleted=False).update(is_deleted=True,
                                                                                           deletedtime=datetime.datetime.now(),
                                                                                           deleteduser=request.user)
                        projindustrylist = []
                        for industry in addlist:
                            projindustrylist.append(projectIndustries(proj=pro, industry=industry, createuser=request.user))
                        pro.project_industries.bulk_create(projindustrylist)

                    if transactiontypedata:
                        transactionTypelist = TransactionType.objects.in_bulk(tagsdata)
                        addlist = [item for item in transactionTypelist if item not in pro.transactionType.all()]
                        removelist = [item for item in pro.transactionType.all() if item not in transactionTypelist]
                        pro.project_TransactionTypes.filter(transactionType__in=removelist, is_deleted=False).update(is_deleted=True,
                                                                                           deletedtime=datetime.datetime.now(),
                                                                                           deleteduser=request.user)
                        projtransactiontypelist = []
                        for transactionPhase in addlist:
                            projtransactiontypelist.append(projectTransactionType(proj=pro, transactionType=transactionPhase, createuser=request.user))
                        pro.project_TransactionTypes.bulk_create(projtransactiontypelist)

                else:
                    raise InvestError(code=4001,
                                      msg='data有误_%s\n%s' % (proj.error_messages, proj.errors))
                return JSONResponse(
                    {'success': True, 'result': returnDictChangeToLanguage(ProjSerializer(pro).data,lang), 'errorcode': 1000, 'errormsg': None})
        except InvestError as err:
            return JSONResponse({'success': False, 'result': None, 'errorcode': err.code, 'errormsg': err.msg})
        except Exception:
            catchexcption(request)
            return JSONResponse({'success': False, 'result': None, 'errorcode': 9999,
                                 'errormsg': traceback.format_exc().split('\n')[-2]})

    @loginTokenIsAvailable()
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            lang = request.GET.get('lang')
            if request.user.has_perm('proj.admin_deleteproj'):
                pass
            elif request.user.has_perm('proj.user_deleteproj',instance):
                pass
            else:
                raise InvestError(code=2009)
            rel_fileds = [f for f in instance._meta.get_fields() if isinstance(f, ForeignObjectRel)]
            links = [f.get_accessor_name() for f in rel_fileds]
            for link in links:
                manager = getattr(instance, link, None)
                if not manager:
                    continue
                # one to one
                if isinstance(manager, models.Model):
                    if hasattr(manager, 'is_deleted') and not manager.is_deleted:
                        raise InvestError(code=2010, msg=u'{} 上有关联数据'.format(link))
                else:
                    try:
                        manager.model._meta.get_field('is_deleted')
                        if manager.all().filter(is_deleted=False).count():
                            raise InvestError(code=2010, msg=u'{} 上有关联数据'.format(link))
                    except FieldDoesNotExist as ex:
                        if manager.all().count():
                            raise InvestError(code=2010, msg=u'{} 上有关联数据'.format(link))
            with transaction.atomic():
                instance.is_deleted = True
                instance.deleteduser = request.user
                instance.deletetime = datetime.datetime.now()
                instance.save()
                response = {'success': True, 'result': returnDictChangeToLanguage(ProjSerializer(instance).data,lang), 'errorcode': 1000,
                            'errormsg': None}
                return JSONResponse(response)
        except InvestError as err:
            return JSONResponse({'success': False, 'result': None, 'errorcode': err.code, 'errormsg': err.msg})
        except Exception:
            catchexcption(request)
            return JSONResponse({'success': False, 'result': None, 'errorcode': 9999,
                                 'errormsg': traceback.format_exc().split('\n')[-2]})



class ProjFinanceView(viewsets.ModelViewSet):

    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend,)
    queryset = finance.objects.all().filter(is_deleted=False)
    filter_fields = ('proj', 'netIncome',)
    serializer_class = FinanceSerializer
    redis_key = 'projectFinanace'
    Model = finance


    def get_queryset(self):
        if self.request.user.is_anonymous:
            raise InvestError(code=8889)
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all().filter(datasource=self.request.user.datasource)
        else:
            raise InvestError(code=8890)
        return queryset

    def get_object(self, pk=None):
        if pk:
            obj = read_from_cache(self.redis_key + '_%s' % pk)
            if not obj:
                try:
                    obj = self.queryset.get(id=pk)
                except finance.DoesNotExist:
                    raise InvestError(code=40031)
                else:
                    write_to_cache(self.redis_key + '_%s' % pk, obj)
        else:
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
            )
            obj = read_from_cache(self.redis_key + '_%s' % self.kwargs[lookup_url_kwarg])
            if not obj:
                try:
                    obj = self.queryset.get(id=self.kwargs[lookup_url_kwarg])
                except finance.DoesNotExist:
                    raise InvestError(code=40031)
                else:
                    write_to_cache(self.redis_key + '_%s' % self.kwargs[lookup_url_kwarg], obj)
        if obj.datasource != self.request.user.datasource:
            raise InvestError(code=8888, msg='资源非同源')
        return obj

    @loginTokenIsAvailable()
    def list(self, request, *args, **kwargs):
        page_size = request.GET.get('page_size')
        page_index = request.GET.get('page_index')  # 从第一页开始
        lang = request.GET.get('lang')
        if not page_size:
            page_size = 10
        if not page_index:
            page_index = 1
        queryset = self.filter_queryset(self.get_queryset())
        if not request.user.has_perm('proj.admin_getproj'):
            queryset = queryset
        else:
            queryset = queryset.filter(proj__createuser__id=request.user.id)
        try:
            queryset = Paginator(queryset, page_size)
        except EmptyPage:
            return JSONResponse({'success': True, 'result': [], 'errorcode': 1000, 'errormsg': None})
        queryset = queryset.page(page_index)
        serializer = FinanceSerializer(queryset, many=True)
        return JSONResponse({'success': True, 'result': returnListChangeToLanguage(serializer.data,lang), 'errorcode': 1000, 'errormsg': None})

    @loginTokenIsAvailable()
    def create(self, request, *args, **kwargs):
        data = request.data
        projid = request.GET.get('project')
        try:
            proj = project.objects.get(id=projid,is_deleted=False,datasource=request.user.datasource)
        except project.DoesNotExist:
            raise InvestError(code=4002,msg='指定内容不存在')
        if request.user.datasource != proj.datasource:
            raise InvestError(code=8888,msg='数据不同源')
        elif request.user.has_perm('proj.admin_changeproj'):
            pass
        elif request.user.has_perm('proj.user_changeproj',proj):
            pass
        else:
            raise InvestError(code=2009,msg='没有增加该项目财务信息的权限')
        lang = request.GET.get('lang')
        financedata = data.get('finances')
        try:
            with transaction.atomic():
                if financedata:
                    for f in financedata:
                        f['proj'] = proj.pk
                        f['createuser'] = request.user.id
                        f['datasource'] = request.user.datasource.id
                    finances = FinanceCreateSerializer(data=financedata,many=True)
                    if finances.is_valid():
                       finances.save()
                    else:
                        raise InvestError(code=4001,
                                          msg='财务信息有误_%s\n%s' % (finances.error_messages, finances.errors))
                else:
                    raise InvestError(code=20071,msg='finances field cannot be null')
                return JSONResponse(
                    {'success': True, 'result': returnListChangeToLanguage(finances.data,lang), 'errorcode': 1000, 'errormsg': None})
        except InvestError as err:
            return JSONResponse({'success': False, 'result': None, 'errorcode': err.code, 'errormsg': err.msg})
        except Exception:
            catchexcption(request)
            return JSONResponse({'success': False, 'result': None, 'errorcode': 9999,
                                 'errormsg': traceback.format_exc().split('\n')[-2]})

    @loginTokenIsAvailable()
    def update(self, request, *args, **kwargs):
        data = request.data
        lang = request.GET.get('lang')
        financedata = data.get('finances')
        try:
            with transaction.atomic():
                if financedata:
                    newfinances = []
                    for f in financedata:
                        fid = f['id']
                        projfinance = self.get_object(fid)
                        if request.user.has_perm('proj.admin_changeproj'):
                            pass
                        elif request.user.has_perm('proj.user_changeproj',projfinance.proj):
                            pass
                        else:
                            raise InvestError(code=2009)
                        f['lastmodifyuser'] = request.user.id
                        f['lastmodifytime'] = datetime.datetime.now()
                        finance = FinanceChangeSerializer(projfinance,data=financedata)
                        if finance.is_valid():
                            finance.save()
                        else:
                            raise InvestError(code=4001,
                                          msg='财务信息有误_%s\n%s' % (finance.error_messages, finance.errors))
                        newfinances.append(finance.data)
                else:
                    raise InvestError(code=20071, msg='finances field cannot be null')
                return JSONResponse(
                    {'success': True, 'result': returnListChangeToLanguage(newfinances, lang), 'errorcode': 1000,
                     'errormsg': None})
        except InvestError as err:
            return JSONResponse({'success': False, 'result': None, 'errorcode': err.code, 'errormsg': err.msg})
        except Exception:
            catchexcption(request)
            return JSONResponse({'success': False, 'result': None, 'errorcode': 9999,
                                 'errormsg': traceback.format_exc().split('\n')[-2]})

    @loginTokenIsAvailable()
    def destroy(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                financeidlist = request.data
                if not isinstance(finance,list):
                    raise InvestError(code=20071,msg='expect an list')
                lang = request.GET.get('lang')
                returnlist = []
                for projfinanceid in financeidlist:
                    projfinance = self.get_object(projfinanceid)
                    if request.user.has_perm('proj.user_deleteproj', projfinance.proj):
                        pass
                    elif request.user.has_perm('proj.admin_deleteproj'):
                        pass
                    else:
                        raise InvestError(code=2009, msg='没有权限')
                    projfinance.is_deleted = True
                    projfinance.deleteduser = request.user
                    projfinance.deletedtime = datetime.datetime.now()
                    projfinance.save()
                    returnlist.append(FinanceSerializer(projfinance).data)
                response = {'success': True,'result': returnListChangeToLanguage(returnlist,lang).data, 'errorcode': 1000, 'errormsg': None}
                return JSONResponse(response)
        except InvestError as err:
            return JSONResponse({'success': False, 'result': None, 'errorcode': err.code, 'errormsg': err.msg})
        except Exception:
            catchexcption(request)
            return JSONResponse({'success': False, 'result': None, 'errorcode': 9999,
                                 'errormsg': traceback.format_exc().split('\n')[-2]})

class ProjectFavoriteView(viewsets.ModelViewSet):
    filter_backends = (filters.DjangoFilterBackend,)
    queryset = favoriteProject.objects.all().filter(is_deleted=False)
    filter_fields = ('proj', 'user','trader','favoritetype')
    serializer_class = FavoriteSerializer
    Model = favoriteProject

    def get_queryset(self):
        if self.request.user.is_anonymous:
            raise InvestError(code=8889)
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )
        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.filter(datasource=self.request.user.datasource)
        else:
            raise InvestError(code=8890)
        return queryset

    def get_object(self, pk=None):
        if pk:
            try:
                obj = self.queryset.get(id=pk)
            except finance.DoesNotExist:
                raise InvestError(code=40031)
        else:
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
            )
            try:
                obj = self.queryset.get(id=self.kwargs[lookup_url_kwarg])
            except finance.DoesNotExist:
                raise InvestError(code=40031)
        if obj.datasource != self.request.user.datasource:
            raise InvestError(code=8888, msg='资源非同源')
        return obj


    def list(self, request, *args, **kwargs):
        page_size = request.GET.get('page_size')
        page_index = request.GET.get('page_index')  # 从第一页开始
        lang = request.GET.get('lang')
        userid = request.GET.get('user')
        ftype = request.GET.get('favoritetype')
        if not ftype:
            raise InvestError(code=20072,msg='favoritetype cannot be null')
        if not page_size:
            page_size = 10
        if not page_index:
            page_index = 1
        queryset = self.filter_queryset(self.get_queryset())
        if not userid:
            queryset = queryset.filter(user=request.user)
        if request.user.is_anonymous:
            queryset = queryset.filter(isHidden=False)
        else:
            if request.user.has_perm('proj.admin_getproj'):
                pass
            else:
                queryset = queryset.filter(Q(isHidden=False) | Q(createuser=request.user))
        try:
            queryset = Paginator(queryset, page_size)
        except EmptyPage:
            return JSONResponse({'success': True, 'result': [], 'errorcode': 1000, 'errormsg': None})
        queryset = queryset.page(page_index)
        serializer = ProjCommonSerializer(queryset, many=True)
        return JSONResponse({'success': True, 'result': returnListChangeToLanguage(serializer.data,lang), 'errorcode': 1000, 'errormsg': None})

    # 批量增加，接受projidlist
    @loginTokenIsAvailable()
    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            lang = request.GET.get('lang')
            userid = data.get('user')
            ftype = data.get('favoritetype')
            data['createuser'] = request.user.id
            data['datasource'] = request.user.datasource.id
            projidlist = data.pop('projs',None)
            try:
                user = MyUser.objects.get(id=userid,datasource=request.user.datasource,is_deleted=False)
            except MyUser.DoesNotExist:
                raise InvestError(code=2002)
            if request.user == user:
                if ftype not in [1,2]:
                    raise InvestError(code=4005)
            elif request.user.has_perm('proj.admin_addfavorite'):
                if ftype not in [3,4]:
                    raise InvestError(code=4005)
            elif request.user.has_perm('proj.user_addfavorite',user):
                if ftype != 5:
                    raise InvestError(code=4005)
            else:
                raise InvestError(code=2009)
            with transaction.atomic():
                favoriteProjectList = []
                for projid in projidlist:
                    data['proj'] = projid
                    newfavorite = FavoriteSerializer(data=data)
                    if newfavorite.is_valid():
                        if newfavorite.validated_data.user.datasource != request.user.datasource or newfavorite.validated_data.proj.datasource != request.user.datasource or\
                                (newfavorite.validated_data.trader and newfavorite.validated_data.trader.datasource != request.user.datasource):
                            raise InvestError(code=8888)
                        newfavorite.save()
                        favoriteProjectList.append(newfavorite.data)
                        response = {'success': True, 'result':returnDictChangeToLanguage(newfavorite.data,lang),'errorcode':1000,'errormsg':None}
                    else:
                        raise InvestError(code=20071,msg='%s'%newfavorite.errors)
                    return JSONResponse(response)
        except InvestError as err:
            return JSONResponse({'success': False, 'result': None, 'errorcode': err.code, 'errormsg': err.msg})
        except Exception:
            catchexcption(request)
            return JSONResponse({'success': False, 'result': None, 'errorcode': 9999,
                                 'errormsg': traceback.format_exc().split('\n')[-2]})
    #批量删除
    @loginTokenIsAvailable()
    def destroy(self, request, *args, **kwargs):
        try:
            favoridlist = request.data
            userlist = []
            lang = request.GET.get('lang')
            if not favoridlist:
                raise InvestError(code=20071, msg='except a not null list')
            with transaction.atomic():
                for favorid in favoridlist:
                    instance = self.get_object(favorid)
                    if request.user.has_perm('proj.admin_deletefavorite') or request.user == instance.user:
                        pass
                    else:
                        raise InvestError(code=2009)
                    instance.is_deleted = True
                    instance.deleteduser = request.user
                    instance.deletedtime = datetime.datetime.utcnow()
                    instance.save()
                    userlist.append(FavoriteSerializer(instance).data)
                response = {'success': True, 'result': returnListChangeToLanguage(userlist, lang), 'errorcode': 1000,
                            'errormsg': None}
                return JSONResponse(response)
        except InvestError as err:
            return JSONResponse({'success': False, 'result': None, 'errorcode': err.code, 'errormsg': err.msg})
        except Exception:
            catchexcption(request)
            return JSONResponse({'success': False, 'result': None, 'errorcode': 9999,
                                 'errormsg': traceback.format_exc().split('\n')[-2]})
