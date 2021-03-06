#coding=utf-8
from __future__ import unicode_literals

import datetime
from django.db import models

from proj.models import project
from sourcetype.models import DataSource
from usersys.models import MyUser
from utils.customClass import InvestError, MyForeignKey, MyModel


class publicdirectorytemplate(MyModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64,blank=True,null=True)
    parent = MyForeignKey('self',blank=True,null=True)
    orderNO = models.PositiveSmallIntegerField()
    deleteduser = MyForeignKey(MyUser, blank=True, null=True, related_name='userdelete_publicdirectorytemplate')
    createuser = MyForeignKey(MyUser, blank=True, null=True, related_name='usercreate_publicdirectorytemplate')
    lastmodifyuser = MyForeignKey(MyUser, blank=True, null=True, related_name='usermodify_publicdirectorytemplate')
    class Meta:
        db_table = 'dataroompublicdirectorytemplate'

class dataroom(MyModel):
    id = models.AutoField(primary_key=True)
    proj = MyForeignKey(project,related_name='proj_datarooms',help_text='dataroom关联项目')
    isClose = models.BooleanField(help_text='是否关闭',blank=True,default=False)
    closeDate = models.DateTimeField(blank=True,null=True,help_text='关闭日期')
    deleteduser = MyForeignKey(MyUser, blank=True, null=True, related_name='userdelete_datarooms')
    createuser = MyForeignKey(MyUser, blank=True, null=True, related_name='usercreate_datarooms')
    lastmodifyuser = MyForeignKey(MyUser, blank=True, null=True, related_name='usermodify_datarooms')
    datasource = MyForeignKey(DataSource, blank=True, null=True, help_text='数据源')
    class Meta:
        db_table = 'dataroom'
        permissions = (
            ('admin_getdataroom','管理员查看dataroom'),
            ('admin_changedataroom', '管理员修改dataroom里的文件/控制用户可见文件范围'),
            ('admin_deletedataroom', '管理员删除dataroom'),
            ('admin_adddataroom', '管理员添加dataroom'),
            ('admin_closedataroom', '管理员关闭dataroom'),
            ('downloadDataroom','打包下载dataroom'),
            ('user_adddataroomfile', '用户上传dataroom文件'),
            ('user_deletedataroomfile', '用户删除dataroom文件'),
        )

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.proj:
            raise InvestError(code=7004,msg='proj缺失')
        if self.proj.projstatus_id < 4:
            raise InvestError(5003,msg='项目尚未终审发布')
        super(dataroom, self).save(force_insert, force_update, using, update_fields)

class dataroomdirectoryorfile(MyModel):
    id = models.AutoField(primary_key=True)
    dataroom = MyForeignKey(dataroom,related_name='dataroom_directories',help_text='目录或文件所属dataroom')
    parent = MyForeignKey('self',blank=True,null=True,related_name='asparent_directories',help_text='目录或文件所属目录id')
    orderNO = models.PositiveSmallIntegerField(help_text='目录或文件在所属目录下的排序位置',blank=True,default=0)
    size = models.IntegerField(blank=True,null=True,help_text='文件大小')
    filename = models.CharField(max_length=128,blank=True,null=True,help_text='文件名或目录名')
    realfilekey = models.CharField(max_length=128,blank=True,null=True,help_text='原文件key')
    key = models.CharField(max_length=128,blank=True,null=True,help_text='文件路径')
    bucket = models.CharField(max_length=128,blank=True,default='file',help_text='文件所在空间')
    isFile = models.BooleanField(blank=True,default=False,help_text='true/文件，false/目录')
    deleteduser = MyForeignKey(MyUser, blank=True, null=True, related_name='userdelete_dataroomdirectories')
    createuser = MyForeignKey(MyUser, blank=True, null=True, related_name='usercreate_dataroomdirectories')
    lastmodifyuser = MyForeignKey(MyUser, blank=True, null=True, related_name='usermodify_dataroomdirectories')
    datasource = MyForeignKey(DataSource, blank=True, null=True, help_text='数据源')
    class Meta:
        db_table = 'dataroomdirectoryorfile'

    def save(self, force_insert=False, force_update=False, using=None,update_fields=None):
        if self.isFile:
            try:
                if self.pk:
                    dataroomdirectoryorfile.objects.exclude(pk=self.pk).get(is_deleted=False, key=self.key)
                else:
                    dataroomdirectoryorfile.objects.get(is_deleted=False, key=self.key)
            except dataroomdirectoryorfile.DoesNotExist:
                pass
            else:
                raise InvestError(code=7001,msg='相同key文件已存在')
        if self.pk is None:
            if self.dataroom.isClose or self.dataroom.is_deleted:
                raise InvestError(7012, msg='dataroom已关闭/删除，无法添加文件/目录')
        if self.parent:
            if self.parent.isFile:
                raise InvestError(7007,msg='非目录结构不能存储文件')
        if self.filename is None:
            raise InvestError(2007,msg='名称不能为空')
        super(dataroomdirectoryorfile, self).save(force_insert, force_update, using, update_fields)


class dataroom_User_file(MyModel):
    dataroom = MyForeignKey(dataroom, blank=True, null=True, related_name='dataroom_users')
    user = MyForeignKey(MyUser, blank=True, null=True, related_name='user_datarooms', help_text='投资人')
    files = models.ManyToManyField(dataroomdirectoryorfile, blank=True)
    trader = MyForeignKey(MyUser, blank=True, null=True, help_text='交易师', related_name='trader_datarooms')
    deleteduser = MyForeignKey(MyUser, blank=True, null=True, related_name='userdelete_userdatarooms')
    createuser = MyForeignKey(MyUser, blank=True, null=True, related_name='usercreate_userdatarooms')
    datasource = MyForeignKey(DataSource, blank=True, null=True, help_text='数据源')

    class Meta:
        db_table = 'dataroom_user'

    def save(self, force_insert=False, force_update=False, using=None,update_fields=None):
        if not self.trader or not self.user:
            raise InvestError(2007, '投资人或交易师不能为空')
        if self.pk is None:
            if self.dataroom.isClose or self.dataroom.is_deleted:
                raise InvestError(7012,msg='dataroom已关闭/删除，无法添加用户')
            try:
                dataroom_User_file.objects.get(is_deleted=False, user=self.user, dataroom=self.dataroom)
            except dataroom_User_file.DoesNotExist:
                pass
            else:
                raise InvestError(code=2004, msg='用户已存在一个相同项目的dataroom了')
        super(dataroom_User_file, self).save(force_insert, force_update, using, update_fields)