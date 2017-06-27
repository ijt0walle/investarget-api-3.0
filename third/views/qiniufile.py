#coding=utf-8


# Create your views here.
import datetime
import traceback

import qiniu
import time

from qiniu import BucketManager
from qiniu import put_data
from qiniu.services.storage.uploader import _Resume, put_file
from rest_framework.decorators import api_view

from utils.customClass import JSONResponse, InvestError, MyUploadProgressRecorder
from utils.util import InvestErrorResponse, ExceptionResponse, SuccessResponse

ACCESS_KEY = 'NJkzgfMrIi-wL_gJyeLfU4dSqXyk5eeGrI7COPPu'
SECRET_KEY = '6hWJqsm9xdAcGFPyr-MHwVKpdrQ25eJbf2JsaQ8U'

qiniu_url = {
    'file':'o7993llwa.qnssl.com',
    'image':'o79atf82v.qnssl.com',
}
# 是使用的队列名称,不设置代表不使用私有队列，使用公有队列。
pipeline = 'aszxsddsfcsc'
# 设置转码参数
fops = 'yifangyun_preview/v2'




def qiniuupload(request):
    try:
        bucket_name = request.GET.get('bucket')
        data_dict = request.FILES
        uploaddata = None
        if bucket_name not in qiniu_url.keys():
            raise InvestError(2020,msg='bucket error')
        for key in data_dict.keys():
            uploaddata = data_dict[key]
        q = qiniu.Auth(ACCESS_KEY, SECRET_KEY)
        filetype = str(uploaddata.name).split('.')[-1]
        if filetype != 'pdf':
            saveas_key = qiniu.urlsafe_base64_encode('file:%s' % (str(uploaddata.name).split('.')[0] + '.pdf'))
            persistentOps = fops + '|saveas/' + saveas_key
            policy = {
                'persistentOps': persistentOps,
                # 'persistentPipeline': pipeline,
                'deleteAfterDays': 1,
            }
        else:
            policy = None
        key = str(uploaddata.name)   #key 文件名
        token = q.upload_token(bucket_name, key, 3600,policy=policy)
        ret, info = put_data(token, key, uploaddata)
        return_url= None
        if info is not None:
            if info.status_code == 200:
                return_url = getUrlWithBucketAndKey(bucket_name, ret['key'])
            else:
                raise InvestError(2020,msg=str(info))
        return JSONResponse(SuccessResponse({'key':key,'url':return_url}))
    except InvestError as err:
        return JSONResponse(InvestErrorResponse(err))
    except Exception:
        return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

#上传本地文件
def qiniuuploadfilepath(filepath, bucket_name):
    q = qiniu.Auth(ACCESS_KEY, SECRET_KEY)
    filetype = filepath.split('.')[-1]
    key = "%s.%s" % (str(time.time()), filetype)   # key 文件名
    print key
    token = q.upload_token(bucket_name, key, 3600, policy={}, strict_policy=True)
    ret, info = put_file(token, key, filepath)
    if info is not None:
        if info.status_code == 200:
            return True, "http://%s/%s" % (qiniu_url['file'], ret["key"]),key
        else:
            return False, str(info),None
    else:
        return False,None,None





@api_view(['POST'])
def bigfileupload(request):
    """
    分片上传
    """
    try:
        bucket_name = request.GET.get('bucket')
        if bucket_name not in qiniu_url.keys():
            raise InvestError(2020,msg='bucket error')
        data_dict = request.FILES
        uploaddata = None
        for key in data_dict.keys():
            uploaddata = data_dict[key]
        q = qiniu.Auth(ACCESS_KEY, SECRET_KEY)
        filetype = str(uploaddata.name).split('.')[-1]
        key = str(uploaddata.name)  # key 文件名
        # key = datetime.datetime.strftime('%d/%m/%Y %H:%M') + filetype
        if filetype != 'pdf':
            saveas_key = qiniu.urlsafe_base64_encode('file:%s' % (key.split('.')[0] + '.pdf'))
            persistentOps = fops + '|saveas/' + saveas_key
            policy = {
                'persistentOps': persistentOps,
                # 'persistentPipeline': pipeline,
                'deleteAfterDays': 1,
            }
        else:
            policy = None
        print key
        params = {'x:a':'a'}
        mime_type = uploaddata.content_type
        token = q.upload_token(bucket_name, key, 3600,policy=policy)
        progress_handler = lambda progress,total:progress / total
        uploader = _Resume(token,key,uploaddata,uploaddata.size,params,mime_type,progress_handler,upload_progress_recorder=MyUploadProgressRecorder(),modify_time=None,file_name=key)
        ret,info = uploader.upload()
        print ret
        print '*****'
        print info
        if info is not None:
            if info.status_code == 200:
                return_url = getUrlWithBucketAndKey(bucket_name,ret['key'])
            else:
                raise InvestError(2020,msg=str(info))
        else:
            raise InvestError(2020,msg=str(ret))
        return JSONResponse(SuccessResponse({'key':key,'url':return_url}))
    except InvestError as err:
        return JSONResponse(InvestErrorResponse(err))
    except Exception:
        return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

def getUrlWithBucketAndKey(bucket,key):
    if bucket not in qiniu_url.keys():
        return None
    q = qiniu.Auth(ACCESS_KEY, SECRET_KEY)
    return_url = "https://%s/%s" % (qiniu_url[bucket], key)
    if bucket == 'file':
        return_url = q.private_download_url(return_url)
    return return_url


@api_view(['POST'])
def qiniu_deletefile(request):
    """
    param：{'bucket':str,'key':str}
    """
    try:
        data = request.data
        bucket = data.get('bucket',None)
        key = data.get('key',None)
        if bucket not in qiniu_url.keys():
            return None
        ret, info = deleteqiniufile(bucket,key)
        return  JSONResponse(SuccessResponse({'ret':ret,'info':info}))
    except InvestError as err:
        return JSONResponse(InvestErrorResponse(err))
    except Exception:
        return JSONResponse(ExceptionResponse(traceback.format_exc().split('\n')[-2]))

def deleteqiniufile(bucket,key):
    q = qiniu.Auth(ACCESS_KEY, SECRET_KEY)
    bucketManager = BucketManager(q)
    ret, info = bucketManager.delete(bucket, key)
    return ret, info