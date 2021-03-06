from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin
# Create your views here.
class CartView(View):
    def post(self,request):
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res':0,'errmsg':'请先登陆'})

        if not all([sku_id,count]):
            return JsonResponse({'res':1,'errmsg':'数据不完整'})

        try:
            count = int(count)
        except Exception as f:
            return  JsonResponse({'res':2,'errmsg':'商品数目出错'})

        try:
            sku = GoodsSKU.objects.get(id =sku_id)
        except GoodsSKU.DoesNotExist:
            return  JsonResponse({'res':3,'errmsg':'商品不存在'})

        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        cart_count=conn.hget(cart_key,sku_id)
        if cart_count:
            count += int(cart_count)
        if count>sku.stock:
            return JsonResponse({'res':4,'errmsg':'商品库存不足'})
        conn.hset(cart_key,sku_id,count)
        total_count = conn.hlen(cart_key)

        return JsonResponse({'res':5,'total_count':total_count,'errmsg':'添加成功'})

class CartInfoview(LoginRequiredMixin,View):
    def get(self,request):
        user = request.user
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        cart_dict = conn.hgetall(cart_key)
        skus = []
        total_count = 0
        total_price = 0
        for sku_id,count in cart_dict.items():
            sku = GoodsSKU.objects.get(id = sku_id)
            amount = sku.price*int(count)
            sku.amount = amount
            sku.count = count
            skus.append(sku)
        total_count += int(count)
        total_price += amount

        context = {"total_count":total_count,
                   "total_price":total_price,
                   'skus':skus}
        return  render(request,'cart.html',context)


class CartUpdateView(View):
    def post(self,request):
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登陆'})

        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        try:
            count = int(count)
        except Exception as f:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        conn =get_redis_connection('default')
        cart_key = 'cart_%d'%user.id
        if count>sku.stock:
            return JsonResponse({'res':4,'errmsg':'商品库存不足'})

        conn.hset(cart_key,sku_id,count)

        total_count = 0
        vals=conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        return  JsonResponse({'res':5, 'total_count':total_count,'errmsg':'更新成功'})

class CartDeleteView(View):

    def post(self, request):
        user = request.user

        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登陆'})

        sku_id = request.POST.get('sku_id')

        if not sku_id:
            return  JsonResponse({'res':1,'errmsg':'无效的商品id'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res':2,'errmsg':'商品不存在'})

        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%user.id

        conn.hdel(cart_key,sku_id)
        return JsonResponse({'res':3,'errmsg':'删除成功'})